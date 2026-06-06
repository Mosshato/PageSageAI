"""
AI Teaching Pipeline
--------------------
Runs the full PDF → narration → TTS → ChromaDB pipeline in a background thread.
Also exposes RAG query functions for the ask/reformulate endpoints.

Required packages in Django venv (pip install):
    pymupdf pillow transformers torch
    groq requests
    langchain-google-genai langchain-huggingface langchain-chroma
    langchain-core langchain-text-splitters chromadb sentence-transformers
"""

import json
import os
import sys
import threading
from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv

load_dotenv(Path(settings.BASE_DIR) / '.env')

# ── Add Functionalities scripts to path ─────────────────────────────────────

_FUNC_ROOT = Path(settings.BASE_DIR).parent.parent / "Functionalities"
for _sub in ("PDFExtraction", "RAG"):
    _p = str(_FUNC_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Lazy imports (avoid loading torch/transformers at Django startup) ─────────

def _import_pipeline_modules():
    from textAndImageExtraction import ingest_pdf
    from tableExtraction import narrate_course
    from TTS import generate_audio_for_course
    return ingest_pdf, narrate_course, generate_audio_for_course


def _import_rag_modules():
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableParallel
    from langchain_core.prompts import PromptTemplate
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    return (ChatGoogleGenerativeAI, HuggingFaceEmbeddings, Chroma,
            StrOutputParser, RunnablePassthrough, RunnableParallel,
            PromptTemplate, RecursiveCharacterTextSplitter)

# ── API Keys ──────────────────────────────────────────────────────────────────

GEMINI_API_KEY   = os.environ['GEMINI_API_KEY']
DEEPGRAM_API_KEY = os.environ['DEEPGRAM_API_KEY']

# ── Shared embeddings instance (loaded once per process) ─────────────────────

_embeddings_instance = None
_embeddings_lock = threading.Lock()


def _get_embeddings():
    global _embeddings_instance
    with _embeddings_lock:
        if _embeddings_instance is None:
            _, HuggingFaceEmbeddings, *_ = _import_rag_modules()
            _embeddings_instance = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings_instance


# ── ChromaDB builder ─────────────────────────────────────────────────────────

def build_course_chroma(output_dir: Path, course_id: int):
    """Read narration JSONs from output_dir and add them to the shared OSSU ChromaDB."""
    (_, _, _, _, _, _, _, RecursiveCharacterTextSplitter) = _import_rag_modules()
    _, _, Chroma, *_ = _import_rag_modules()

    narration_files = sorted(
        p for p in output_dir.glob("*_narration.json")
        if p.name != "course_narration.json"
    )
    texts = []
    for nf in narration_files:
        with open(nf, encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("narration_text", "")
        page_num = data.get("page_number", 0)
        if text:
            texts.append(f"[Course {course_id} | Page {page_num}]\n{text}")

    if not texts:
        return

    (_, _, _, _, _, _, _, RecursiveCharacterTextSplitter) = _import_rag_modules()
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    docs = splitter.create_documents(texts)

    (_, _, Chroma, *_) = _import_rag_modules()
    db = Chroma(
        persist_directory=OSSU_CHROMA_DIR,
        embedding_function=_get_embeddings(),
    )
    db.add_documents(docs)


# ── RAG query — folosește baza OSSU existentă ────────────────────────────────

OSSU_CHROMA_DIR = str(_FUNC_ROOT / "RAG" / "chroma_ossu_db")


def query_rag(output_dir: Path, course_id: int, question: str,
              reformulate: bool = False, previous_answer: str = "") -> str:
    (ChatGoogleGenerativeAI, _, Chroma, StrOutputParser,
     RunnablePassthrough, RunnableParallel, PromptTemplate, _) = _import_rag_modules()

    db = Chroma(
        persist_directory=OSSU_CHROMA_DIR,
        embedding_function=_get_embeddings(),
    )
    retriever = db.as_retriever(search_kwargs={"k": 4})

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.3,
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    if reformulate:
        prompt = PromptTemplate.from_template(
            """You are a helpful university professor assistant.

A student asked: {question}

You previously answered: {previous_answer}

The student did not understand. Explain the same concept again but:
- Use a simple everyday analogy anyone can grasp
- Use shorter sentences and avoid jargon
- Be warm and encouraging

Relevant course material:
{context}

Simplified explanation:"""
        )
        from langchain_core.runnables import RunnableLambda
        chain = (
            RunnableParallel(
                context=RunnableLambda(lambda x: x["question"]) | retriever | format_docs,
                question=RunnableLambda(lambda x: x["question"]),
                previous_answer=RunnableLambda(lambda x: x["previous_answer"]),
            )
            | prompt
            | llm
            | StrOutputParser()
        )
        return chain.invoke({"question": question, "previous_answer": previous_answer})
    else:
        prompt = PromptTemplate.from_template(
            """You are a helpful university professor assistant.

Use the course context below to answer the student's question clearly and concisely.
If the context is not relevant, use your general knowledge but mention it.

Course context:
{context}

Student question: {question}

Answer:"""
        )
        chain = (
            RunnableParallel(
                context=retriever | format_docs,
                question=RunnablePassthrough(),
            )
            | prompt
            | llm
            | StrOutputParser()
        )
        return chain.invoke(question)


# ── Background pipeline runner ────────────────────────────────────────────────

def run_pipeline_in_background(course_id: int, pdf_path: Path, output_dir: Path):
    """Launch the full pipeline in a daemon thread."""
    t = threading.Thread(
        target=_run_pipeline,
        args=(course_id, pdf_path, output_dir),
        daemon=True,
    )
    t.start()


def _get_total_pages(output_dir: Path) -> int:
    index_path = output_dir / "course_index.json"
    if not index_path.exists():
        return 0
    with open(index_path, encoding="utf-8") as f:
        return json.load(f).get("total_pages", 0)

def _pdf_page_count(pdf_path: Path) -> int:
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return 0

def _step1_done(output_dir: Path, pdf_path: Path) -> bool:
    total = _get_total_pages(output_dir)
    if total == 0:
        return False
    # Verify the index matches the actual PDF page count
    actual = _pdf_page_count(pdf_path)
    if actual > 0 and total != actual:
        return False
    # Every page PNG must exist
    return all(
        (output_dir / f"page_{i:04d}.png").exists()
        for i in range(1, total + 1)
    )

def _step2_done(output_dir: Path) -> bool:
    total = _get_total_pages(output_dir)
    if total == 0:
        return False
    # Every page narration JSON must exist
    return all(
        (output_dir / f"page_{i:04d}_narration.json").exists()
        for i in range(1, total + 1)
    )

def _step3_done(output_dir: Path) -> bool:
    total = _get_total_pages(output_dir)
    if total == 0:
        return False
    audio_dir = output_dir / "audio"
    # Every page MP3 must exist
    return audio_dir.exists() and all(
        (audio_dir / f"page_{i:04d}.mp3").exists()
        for i in range(1, total + 1)
    )

def _step4_done(output_dir: Path) -> bool:
    return (output_dir / "chroma_indexed.marker").exists()


def _run_pipeline(course_id: int, pdf_path: Path, output_dir: Path):
    from .models import AICourse

    def _update(status=None, step=None, total_pages=None, error_msg=None):
        course = AICourse.objects.get(id=course_id)
        if status is not None:
            course.status = status
        if step is not None:
            course.current_step = step
        if total_pages is not None:
            course.total_pages = total_pages
        if error_msg is not None:
            course.error_msg = error_msg
        course.save()

    print(f"[AI Pipeline] Course {course_id} — started | pdf={pdf_path}", flush=True)

    try:
        ingest_pdf, narrate_course, generate_audio_for_course = _import_pipeline_modules()

        # Step 1 — PDF → PNG + JSON
        if _step1_done(output_dir, pdf_path):
            print(f"[AI Pipeline] Course {course_id} — Step 1: already done, skipping", flush=True)
        else:
            _update(step="EXTRACTING")
            print(f"[AI Pipeline] Course {course_id} — Step 1: extracting PDF pages...", flush=True)
            ingest_pdf(str(pdf_path), str(output_dir))
            print(f"[AI Pipeline] Course {course_id} — Step 1: done", flush=True)

        # Step 2 — JSON → narration text
        if _step2_done(output_dir):
            print(f"[AI Pipeline] Course {course_id} — Step 2: already done, skipping", flush=True)
        else:
            _update(step="NARRATING")
            print(f"[AI Pipeline] Course {course_id} — Step 2: generating narration...", flush=True)
            narrate_course(str(output_dir))
            print(f"[AI Pipeline] Course {course_id} — Step 2: done", flush=True)

        # Step 3 — narration → MP3
        if _step3_done(output_dir):
            print(f"[AI Pipeline] Course {course_id} — Step 3: already done, skipping", flush=True)
        else:
            _update(step="TTS")
            print(f"[AI Pipeline] Course {course_id} — Step 3: generating audio (TTS)...", flush=True)
            generate_audio_for_course(output_dir, api_key=DEEPGRAM_API_KEY)
            print(f"[AI Pipeline] Course {course_id} — Step 3: done", flush=True)

        # Step 4 — Build ChromaDB
        if _step4_done(output_dir):
            print(f"[AI Pipeline] Course {course_id} — Step 4: already done, skipping", flush=True)
        else:
            _update(step="CHROMA")
            print(f"[AI Pipeline] Course {course_id} — Step 4: building ChromaDB...", flush=True)
            build_course_chroma(output_dir, course_id)
            (output_dir / "chroma_indexed.marker").touch()
            print(f"[AI Pipeline] Course {course_id} — Step 4: done", flush=True)

        # Count pages from index
        total_pages = 0
        index_path = output_dir / "course_index.json"
        if index_path.exists():
            with open(index_path, encoding="utf-8") as f:
                idx = json.load(f)
            total_pages = idx.get("total_pages", 0)

        _update(status="READY", step="DONE", total_pages=total_pages)
        print(f"[AI Pipeline] Course {course_id} — READY ({total_pages} pages)", flush=True)

    except Exception as exc:
        _update(status="ERROR", error_msg=str(exc))
        print(f"[AI Pipeline] Course {course_id} — ERROR: {exc}", flush=True)
        raise
