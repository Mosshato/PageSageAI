"""
PDF Ingestion Pipeline
----------------------
Subpasi:
  1.2 - Rasterizare pagini cu PyMuPDF -> PNG
  1.3 - Clasificare semantica cu LayoutLMv3
  1.4 - Structurare JSON per pagina

Dependente:
    pip install pymupdf pillow transformers torch torchvision

Modelul LayoutLMv3 se descarca automat din HuggingFace la primul run.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import fitz  # pymupdf
import torch
from PIL import Image
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification

# ---------------------------------------------------------------------------
# Configuratie
# ---------------------------------------------------------------------------

DPI = 200
OUTPUT_DIR = Path("poze_output")
MODEL_NAME = "microsoft/layoutlmv3-base"

# Mapare etichete model -> tipuri semantice folosite de noi downstream
# LayoutLMv3 fine-tuned pe FUNSD/CORD foloseste etichete B-/I- prefix
# Daca folosesti modelul base fara fine-tuning, facem clasificare euristica
# bazata pe pozitie + font size extras din PyMuPDF (vezi _heuristic_classify)
LABEL_MAP = {
    "B-HEADER":    "title",
    "I-HEADER":    "title",
    "B-QUESTION":  "paragraph",
    "I-QUESTION":  "paragraph",
    "B-ANSWER":    "paragraph",
    "I-ANSWER":    "paragraph",
    "O":           "paragraph",
}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------------------------------------------------------------------
# Structuri de date
# ---------------------------------------------------------------------------

@dataclass
class Block:
    type: str          # title | paragraph | formula | figure | table | bullet
    text: str
    order: int
    bbox: list[float]  # [x0, y0, x1, y1] normalizat 0-1000 (conventie LayoutLMv3)
    confidence: float = 1.0

@dataclass
class PageStructure:
    page_number: int            # 1-indexed
    png_path: str
    width_px: int
    height_px: int
    blocks: list[Block] = field(default_factory=list)
    has_visual_candidate: bool = False  # True daca exista formula sau figure
    raw_text: str = ""

# ---------------------------------------------------------------------------
# 1.2 — Rasterizare
# ---------------------------------------------------------------------------

def rasterize_pdf(pdf_path: str | Path, output_dir: Path, dpi: int = DPI) -> list[dict]:
    """
    Deschide PDF-ul si randeaza fiecare pagina ca PNG.
    Returneaza lista de dicts cu path PNG + text nativ extras.
    """
    pdf_path = Path(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    pages_meta = []

    print(f"[1.2] Rasterizare {len(doc)} pagini la {dpi} DPI...")

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1

        # Render la DPI specificat
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 e DPI-ul default PDF
        pix = page.get_pixmap(matrix=mat, alpha=False)

        png_filename = f"page_{page_num:04d}.png"
        png_path = output_dir / png_filename
        pix.save(str(png_path))

        # Extrage text nativ (fara OCR) cu pozitii
        # get_text("words") returneaza (x0, y0, x1, y1, word, block_no, line_no, word_no)
        words_raw = page.get_text("words")
        raw_text = " ".join(w[4] for w in words_raw)

        # Extrage si blocuri cu font info pentru clasificare euristica
        blocks_raw = page.get_text("dict")["blocks"]

        pages_meta.append({
            "page_number": page_num,
            "png_path": str(png_path),
            "width_px": pix.width,
            "height_px": pix.height,
            "page_width_pt": page.rect.width,   # dimensiuni originale in puncte PDF
            "page_height_pt": page.rect.height,
            "raw_text": raw_text,
            "words_raw": words_raw,
            "blocks_raw": blocks_raw,
        })

        print(f"  Pagina {page_num}/{len(doc)} -> {png_filename} ({pix.width}x{pix.height}px)")

    doc.close()
    return pages_meta

# ---------------------------------------------------------------------------
# 1.3 — Clasificare semantica
# ---------------------------------------------------------------------------

def load_layoutlmv3(model_name: str = MODEL_NAME):
    """
    Incarca procesorul si modelul LayoutLMv3.
    La primul apel descarca ~900MB din HuggingFace.
    """
    print(f"[1.3] Incarcare LayoutLMv3 ({model_name}) pe {DEVICE}...")
    processor = LayoutLMv3Processor.from_pretrained(model_name, apply_ocr=False)
    model = LayoutLMv3ForTokenClassification.from_pretrained(model_name)
    model.to(DEVICE)
    model.eval()
    print("  Model incarcat.")
    return processor, model


def _normalize_bbox(bbox, page_width_pt, page_height_pt) -> list[int]:
    """
    Normalizeaza bbox din puncte PDF la scara 0-1000 (conventie LayoutLMv3).
    bbox = (x0, y0, x1, y1) in puncte PDF
    """
    x0, y0, x1, y1 = bbox
    return [
        int(x0 / page_width_pt * 1000),
        int(y0 / page_height_pt * 1000),
        int(x1 / page_width_pt * 1000),
        int(y1 / page_height_pt * 1000),
    ]


def _heuristic_classify(block_raw: dict, page_height_pt: float) -> str:
    """
    Clasificare euristica bazata pe informatiile de font din PyMuPDF.
    Folosita ca fallback sau complement la LayoutLMv3.

    block_raw vine din page.get_text("dict")["blocks"]
    """
    btype = block_raw.get("type", 0)

    # Tip 1 = imagine embedded in PDF
    if btype == 1:
        return "figure"

    lines = block_raw.get("lines", [])
    if not lines:
        return "paragraph"

    # Colecteaza font sizes din spans
    font_sizes = []
    fonts = []
    all_text = ""
    for line in lines:
        for span in line.get("spans", []):
            font_sizes.append(span.get("size", 12))
            fonts.append(span.get("font", "").lower())
            all_text += span.get("text", "")

    if not font_sizes:
        return "paragraph"

    avg_size = sum(font_sizes) / len(font_sizes)
    text_stripped = all_text.strip()

    # Detectie formula: text scurt, contine simboluri matematice comune
    math_symbols = set("∑∫∂∇αβγδεζηθλμπσφψωΩ=<>±∞√∈∉⊂⊃∪∩")
    has_math = any(c in math_symbols for c in text_stripped)
    looks_like_formula = (
        has_math or
        (len(text_stripped) < 80 and any(op in text_stripped for op in ["=", "→", "⟹", ":=", "O("]))
    )
    if looks_like_formula:
        return "formula"

    # Detectie bullet list
    if text_stripped.startswith(("•", "-", "*", "–", "○", "▪", "►")):
        return "bullet"

    # Detectie titlu: font mare sau bold
    is_bold = any("bold" in f or "heavy" in f for f in fonts)
    if avg_size >= 14 or (avg_size >= 13 and is_bold):
        return "title"

    return "paragraph"


def classify_page_with_layoutlmv3(
    page_meta: dict,
    processor,
    model,
) -> list[Block]:
    """
    Ruleaza LayoutLMv3 pe o pagina si returneaza blocurile clasificate.

    Strategia:
    - Extragem cuvintele cu pozitiile lor (din words_raw de la PyMuPDF)
    - Le trimitem la LayoutLMv3 impreuna cu imaginea PNG
    - Grupam cuvintele in blocuri bazat pe block_no din PyMuPDF
    - Tipul fiecarui bloc e determinat prin vot majoritar al etichetelor LayoutLMv3
      + clasificare euristica pentru formule si figuri
    """
    image = Image.open(page_meta["png_path"]).convert("RGB")
    words_raw = page_meta["words_raw"]      # (x0,y0,x1,y1, word, block_no, line_no, word_no)
    blocks_raw = page_meta["blocks_raw"]
    pw = page_meta["page_width_pt"]
    ph = page_meta["page_height_pt"]

    if not words_raw:
        return []

    words = [w[4] for w in words_raw]
    boxes = [_normalize_bbox((w[0], w[1], w[2], w[3]), pw, ph) for w in words_raw]
    block_nos = [w[5] for w in words_raw]

    # LayoutLMv3 are limita de 512 tokens — trunchiaza daca pagina e foarte densa
    MAX_WORDS = 480
    if len(words) > MAX_WORDS:
        words = words[:MAX_WORDS]
        boxes = boxes[:MAX_WORDS]
        block_nos = block_nos[:MAX_WORDS]

    encoding = processor(
        image,
        words,
        boxes=boxes,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding="max_length",
    )
    encoding = {k: v.to(DEVICE) for k, v in encoding.items()}

    with torch.no_grad():
        outputs = model(**encoding)

    logits = outputs.logits  # (1, seq_len, num_labels)
    predictions = logits.argmax(-1).squeeze().tolist()
    id2label = model.config.id2label

    # Mapeaza predictiile inapoi la cuvinte (primele N tokens dupa [CLS])
    # LayoutLMv3 poate produce mai multi tokens per cuvant, luam primul
    word_ids = encoding.word_ids() if hasattr(encoding, "word_ids") else None

    # Grupeaza cuvintele pe block_no din PyMuPDF
    block_words: dict[int, list] = {}
    for i, (word, block_no) in enumerate(zip(words, block_nos)):
        if block_no not in block_words:
            block_words[block_no] = []
        label_id = predictions[i + 1] if i + 1 < len(predictions) else 0  # +1 pentru [CLS]
        label_str = id2label.get(label_id, "O")
        semantic_type = LABEL_MAP.get(label_str, "paragraph")
        block_words[block_no].append((word, semantic_type))

    # Construieste blocuri finale
    blocks: list[Block] = []
    order = 1

    for block_raw in blocks_raw:
        block_no = block_raw.get("number", -1)

        # Tip figura (imagine embedded)
        if block_raw.get("type") == 1:
            bbox_raw = block_raw.get("bbox", [0, 0, 0, 0])
            blocks.append(Block(
                type="figure",
                text="",
                order=order,
                bbox=_normalize_bbox(bbox_raw, pw, ph),
            ))
            order += 1
            continue

        # Preia cuvintele grupate pentru acest block
        word_label_pairs = block_words.get(block_no, [])
        if not word_label_pairs:
            continue

        block_text = " ".join(w for w, _ in word_label_pairs)
        if not block_text.strip():
            continue

        # Vot majoritar pentru tipul blocului din LayoutLMv3
        from collections import Counter
        type_votes = Counter(lbl for _, lbl in word_label_pairs)
        layoutlm_type = type_votes.most_common(1)[0][0]

        # Override cu clasificare euristica pentru formule si titluri
        # (LayoutLMv3 base fara fine-tuning specific nu e antrenat pe slide-uri)
        heuristic_type = _heuristic_classify(block_raw, ph)
        if heuristic_type in ("formula", "figure", "title"):
            final_type = heuristic_type
        else:
            final_type = layoutlm_type

        bbox_raw = block_raw.get("bbox", [0, 0, 0, 0])
        blocks.append(Block(
            type=final_type,
            text=block_text.strip(),
            order=order,
            bbox=_normalize_bbox(bbox_raw, pw, ph),
        ))
        order += 1

    return blocks

# ---------------------------------------------------------------------------
# 1.4 — Structurare JSON
# ---------------------------------------------------------------------------

def build_page_structure(page_meta: dict, blocks: list[Block]) -> PageStructure:
    has_visual = any(b.type in ("formula", "figure") for b in blocks)
    return PageStructure(
        page_number=page_meta["page_number"],
        png_path=page_meta["png_path"],
        width_px=page_meta["width_px"],
        height_px=page_meta["height_px"],
        blocks=blocks,
        has_visual_candidate=has_visual,
        raw_text=page_meta["raw_text"],
    )


def save_page_json(page_structure: PageStructure, output_dir: Path) -> Path:
    json_path = output_dir / f"page_{page_structure.page_number:04d}.json"
    data = asdict(page_structure)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path

# ---------------------------------------------------------------------------
# Entry point principal
# ---------------------------------------------------------------------------

def ingest_pdf(pdf_path: str | Path, output_dir: str | Path = OUTPUT_DIR) -> list[PageStructure]:
    """
    Functia principala de ingestie.
    Primeste path catre PDF, produce PNG-uri + JSON-uri structurate in output_dir.

    Returneaza lista de PageStructure pentru toate paginile.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # 1.2 Rasterizare
    pages_meta = rasterize_pdf(pdf_path, output_dir)

    # 1.3 Incarcare model (o singura data pentru toate paginile)
    processor, model = load_layoutlmv3()

    results: list[PageStructure] = []

    for page_meta in pages_meta:
        print(f"[1.3] Clasificare semantica pagina {page_meta['page_number']}...")

        blocks = classify_page_with_layoutlmv3(page_meta, processor, model)

        # 1.4 Structurare
        page_structure = build_page_structure(page_meta, blocks)
        json_path = save_page_json(page_structure, output_dir)

        print(f"  -> {len(blocks)} blocuri detectate | visual_candidate={page_structure.has_visual_candidate}")
        print(f"  -> JSON salvat: {json_path}")

        results.append(page_structure)

    # Salveaza si un index global al cursului
    index_path = output_dir / "course_index.json"
    index = {
        "pdf_path": str(pdf_path),
        "total_pages": len(results),
        "pages": [
            {
                "page_number": p.page_number,
                "png_path": p.png_path,
                "json_path": str(output_dir / f"page_{p.page_number:04d}.json"),
                "has_visual_candidate": p.has_visual_candidate,
                "block_types": [b.type for b in p.blocks],
            }
            for p in results
        ],
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] {len(results)} pagini procesate. Index: {index_path}")
    return results


# ---------------------------------------------------------------------------
# Rulare directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Utilizare: python pdf_ingestion.py <cale_pdf> [output_dir]")
        print("Exemplu:   python pdf_ingestion.py curs_algoritmi.pdf poze_output")
        sys.exit(1)

    pdf_file = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "poze_output"

    structures = ingest_pdf(pdf_file, out_dir)

    print("\n=== Sumar ===")
    for ps in structures:
        types = [b.type for b in ps.blocks]
        print(f"  Pagina {ps.page_number}: {types}")