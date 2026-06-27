"""
ChromaDB Builder — OSSU curriculum seeder.
Descarca programa OSSU de pe GitHub si o indexeaza in ChromaDB local.

Dependencies:
    pip install langchain-text-splitters langchain-huggingface langchain-chroma
"""

import re
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


def creaza_baza_de_date(
    persist_directory="./chroma_ossu_db",
    embedding_model="all-MiniLM-L6-v2",
    chunk_size=700,
    chunk_overlap=100,
):
    """
    Parametrii au default-uri identice cu cele folosite la rularea standalone,
    ca sa nu se schimbe comportamentul CLI.
    ai_pipeline.py apeleaza aceasta functie cu valorile din Django
    settings (OSSU_CHROMA_DIR, EMBEDDINGS_MODEL, RAG_CHUNK_SIZE/OVERLAP).
    """
    print("1. Se descarcă programa OSSU...")
    url = "https://raw.githubusercontent.com/ossu/computer-science/master/README.md"
    response = requests.get(url)
    if response.status_code != 200:
        print("Eroare la descărcarea fișierului de pe GitHub.")
        return

    text_complet = response.text

    print("2. Se izolează cursurile principale (Core Computer Science)...")
    pattern = r"(## Core Computer Science.*?)(## Advanced Computer Science)"
    match = re.search(pattern, text_complet, re.DOTALL)

    if not match:
        print("Structura documentului OSSU s-a modificat. Se va folosi tot documentul ca fallback.")
        text_util = text_complet
    else:
        text_util = match.group(1)

    print("3. Se împarte textul în chunk-uri...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.create_documents([text_util])
    print(f"Au fost create {len(chunks)} bucăți de text.")

    print("4. Se încarcă modelul de embeddings (Open-Source)...")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    print("5. Se inițializează și se salvează ChromaDB local...")
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    print(f"Succes! Baza de date a fost salvată în folderul: '{persist_directory}'")


if __name__ == "__main__":
    creaza_baza_de_date()
