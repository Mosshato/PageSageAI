"""
Lecture Narrator
----------------
Receives a page JSON (output from pdf_ingestion.py) and generates
lecture narration in the style of a university professor, using Groq (free).

Dependencies:
    pip install groq python-dotenv

Usage:
    python lecture_narrator.py page_0001.json
    python lecture_narrator.py poze_output/
    python lecture_narrator.py poze_output/ --seconds 60   # forteaza un timp fix pe toate paginile

Timpul de vorbire NU mai e fix pe toate paginile (vechi: 60s/slide peste tot).
Implicit (fara --seconds), fiecare pagina primeste un timp orientativ calculat
din cat de mult/relevant continut are (vezi estimate_target_seconds) — o pagina
de tranzitie sau cu un singur titlu nu trebuie umpluta artificial la 60s, iar
o pagina densa cu o formula importanta merita mai mult timp ca sa fie explicata
bine. --seconds ramane disponibil cand vrei un timp fix, identic pe toate paginile.
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv(Path(__file__).resolve().parent.parent / '.env', encoding='utf-8-sig')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "llama-3.1-8b-instant"
WORDS_PER_MINUTE = 130

# Limite pentru timpul ESTIMAT dinamic (vezi estimate_target_seconds) — nu mai
# folosim un singur numar fix pentru toate paginile.
MIN_SECONDS_PER_SLIDE = 20
MAX_SECONDS_PER_SLIDE = 110

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NarratorConfig:
    # None = timpul se calculeaza per pagina din continut (vezi estimate_target_seconds).
    # Un numar fix forteaza acelasi timp pe toate paginile (comportamentul vechi, util pt teste).
    seconds_per_slide: Optional[int] = None
    model: str = DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Estimare timp orientativ per pagina, pe baza continutului real
# ---------------------------------------------------------------------------

def estimate_target_seconds(blocks: list[dict]) -> int:
    """
    Calculeaza un timp de vorbire orientativ pentru o pagina, in functie de
    cat continut relevant are — nu un numar fix identic pentru toate paginile.

    Logica: ~1 secunda de vorbire la fiecare ~14 caractere de text explicativ
    (aprox ritmul natural de vorbire), plus bonus pentru formule/figuri care
    au nevoie de explicatie suplimentara fata de cat text au efectiv pe slide.
    O pagina cu un singur titlu sau foarte put continut nu va fi umpluta
    artificial; o pagina densa, cu o formula importanta, primeste mai mult timp.
    """
    text_chars = sum(len(b.get("text", "")) for b in blocks if b.get("type") != "figure")
    has_formula = any(b.get("type") == "formula" for b in blocks)
    has_figure = any(b.get("type") == "figure" and b.get("text") for b in blocks)

    estimated = text_chars / 14.0
    if has_formula:
        estimated += 15  # formulele cer explicatie verbala suplimentara, nu doar citire
    if has_figure:
        estimated += 10  # idem pentru o figura cu descriere reala de explicat

    return int(min(MAX_SECONDS_PER_SLIDE, max(MIN_SECONDS_PER_SLIDE, estimated)))

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

BLOCK_TYPE_DESCRIPTIONS = {
    "title":     "section or chapter title",
    "paragraph": "explanatory paragraph",
    "formula":   "mathematical formula or technical expression",
    "figure":    "figure, diagram, or image",
    "table":     "data table",
    "bullet":    "bullet list of key points",
}


def _describe_blocks(blocks: list[dict]) -> str:
    lines = []
    for block in blocks:
        btype = block.get("type", "paragraph")
        text = block.get("text", "").strip()
        label = BLOCK_TYPE_DESCRIPTIONS.get(btype, btype)
        if btype == "figure":
            if text:
                lines.append(f"[{label.upper()}] What the image actually shows: {text}")
            else:
                lines.append(f"[{label.upper()}] — embedded image, no description available (describe contextually)")
        elif text:
            lines.append(f"[{label.upper()}] {text}")
    return "\n".join(lines)


def build_prompt(page_data: dict, config: NarratorConfig) -> str:
    page_number = page_data.get("page_number", "?")
    blocks = page_data.get("blocks", [])
    # Daca config forteaza un timp fix il respectam (ex: CLI --seconds); altfel
    # timpul e calculat per pagina din cat continut relevant are (vezi functia).
    target_seconds = config.seconds_per_slide if config.seconds_per_slide is not None else estimate_target_seconds(blocks)
    target_words = int((target_seconds / 60) * WORDS_PER_MINUTE)
    # Range mai larg (±30%) decat inainte (±15%) — vrem ca modelul sa aleaga
    # lungimea potrivita continutului, nu sa nimereasca exact un numar fix.
    target_words_range = f"{int(target_words * 0.7)}–{int(target_words * 1.3)}"
    blocks_text = _describe_blocks(blocks)
    has_formula = any(b.get("type") == "formula" for b in blocks)
    has_figure = any(b.get("type") == "figure" for b in blocks)

    special_instructions = []
    if has_formula:
        special_instructions.append(
            "- This slide contains MATHEMATICAL FORMULAS. "
            "Do NOT read them out character by character. "
            "Instead, explain what the formula represents, what it computes, and why it matters. "
            "Use natural verbal language: 'the minimum distance to node v equals...'"
        )
    if has_figure:
        special_instructions.append(
            "- This slide contains a FIGURE or DIAGRAM. "
            "Explicitly tell students to look at the image on the slide. "
            "Describe what they should observe visually and what conclusion to draw from it. "
            "Example: 'Look at the diagram on your slide — notice how the nodes at each level...'"
        )
    if not special_instructions:
        special_instructions.append(
            "- Present the information clearly and progressively, from general to specific."
        )

    special_block = "\n".join(special_instructions)

    return f"""You are an experienced university professor in a computer science or exact sciences faculty.
You are delivering a live lecture to your third-year students. Your tone is calm, clear, and slightly
conversational — like a great lecturer, not a textbook being read aloud.

You have in front of you the content from SLIDE {page_number} of the course presentation:

---
{blocks_text}
---

YOUR TASK:
Generate the exact words you will speak aloud during class for this slide.
As a rough guide, aim for around {target_words_range} words (~{target_seconds}s of speaking) —
but this is a GUIDELINE based on how much this specific slide actually contains, not a fixed
quota every slide must hit. Use your judgment:
- If the slide is a short transition, a section title, or has very little to explain, speak briefly and move on — do NOT pad it with filler just to reach a word count.
- If the slide contains a dense, important, or hard-to-grasp concept (a key formula, a subtle distinction, a result everything else builds on), take the time it actually needs, even if that means going longer than the guide.

MANDATORY RULES:
- Address students directly or use first-person plural: "Now we'll see...", "Notice that...", "Let's think about this together...", "I want you to focus on..."
- Do NOT open with "Good morning" or "In this lecture we will learn" — jump straight into the subject as if the lecture is already underway
- Do NOT repeat the slide text word for word — rephrase, explain, provide context and intuition
- If a concept is abstract, give a concrete example or a simple analogy students can relate to
- Transitions between blocks must feel natural, as in real speech
- End with a short bridging sentence that either prepares the next slide or reinforces the core takeaway
{special_block}
- Reply with ONLY the spoken text — no titles, no brackets, no meta-commentary like "Here is the narration:"

LANGUAGE: English"""

# ---------------------------------------------------------------------------
# Rate limit: parse wait time from error message
# ---------------------------------------------------------------------------

def _parse_wait_seconds(error_message: str) -> float:
    """
    Groq returns something like 'Please try again in 3m12.672s.'
    Parses that into total seconds. Defaults to 60s if unparseable.
    """
    match = re.search(r'in\s+(?:(\d+)m)?(\d+(?:\.\d+)?)s', error_message)
    if match:
        minutes = int(match.group(1) or 0)
        seconds = float(match.group(2) or 0)
        return minutes * 60 + seconds + 2  # +2s buffer
    return 60.0

# ---------------------------------------------------------------------------
# LLM call with retry on rate limit
# ---------------------------------------------------------------------------

def generate_narration(
    page_data: dict,
    config: NarratorConfig,
    api_key: Optional[str] = None,
    max_retries: int = 5,
) -> str:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=key)
    prompt = build_prompt(page_data, config)

    target_seconds = config.seconds_per_slide if config.seconds_per_slide is not None else estimate_target_seconds(page_data.get("blocks", []))
    print(f"  [LLM] Model: {config.model} | Target: ~{target_seconds}s "
          f"(~{int(target_seconds / 60 * WORDS_PER_MINUTE)} words, "
          f"{'fixed' if config.seconds_per_slide is not None else 'auto'})")

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a university professor generating spoken lecture narration for academic courses. "
                            "Your responses are direct, clear, and ready to be read aloud. "
                            "You never add explanations about what you did or any markdown formatting."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            wait = _parse_wait_seconds(str(e))
            print(f"  [Rate limit] Attempt {attempt}/{max_retries}. "
                  f"Waiting {wait:.1f}s before retrying...")
            time.sleep(wait)

    raise RuntimeError(f"Failed after {max_retries} retries due to rate limiting.")

# ---------------------------------------------------------------------------
# Duration estimation
# ---------------------------------------------------------------------------

def estimate_duration(text: str) -> float:
    return round(len(text.split()) / WORDS_PER_MINUTE * 60, 1)

# ---------------------------------------------------------------------------
# Single page — skips if narration already exists
# ---------------------------------------------------------------------------

def narrate_page(
    json_path: str | Path,
    seconds_per_slide: Optional[int] = None,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    save_output: bool = True,
) -> dict:
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found: {json_path}")

    # --- RESUME: skip if narration file already exists ---
    out_path = json_path.parent / json_path.name.replace(".json", "_narration.json")
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)
        page_num = existing.get("page_number", "?")
        print(f"[Skip] Page {page_num} — narration already exists ({out_path.name})")
        return existing

    with open(json_path, encoding="utf-8") as f:
        page_data = json.load(f)

    config = NarratorConfig(seconds_per_slide=seconds_per_slide, model=model)

    print(f"[Narrator] Page {page_data.get('page_number', '?')} | "
          f"Blocks: {len(page_data.get('blocks', []))} | "
          f"Visual candidate: {page_data.get('has_visual_candidate', False)}")

    narration = generate_narration(page_data, config, api_key)
    word_count = len(narration.split())
    estimated_seconds = estimate_duration(narration)
    target_seconds_used = seconds_per_slide if seconds_per_slide is not None else estimate_target_seconds(page_data.get("blocks", []))

    result = {
        "page_number": page_data.get("page_number"),
        "narration_text": narration,
        "word_count": word_count,
        "estimated_seconds": estimated_seconds,
        "target_seconds": target_seconds_used,
        "target_mode": "fixed" if seconds_per_slide is not None else "auto",
        "model_used": model,
        "blocks_used": len(page_data.get("blocks", [])),
        "has_visual_candidate": page_data.get("has_visual_candidate", False),
    }

    if save_output:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  [Saved] {out_path.name}")

    return result

# ---------------------------------------------------------------------------
# Full course
# ---------------------------------------------------------------------------

def narrate_course(
    course_dir: str | Path,
    seconds_per_slide: Optional[int] = None,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
) -> list[dict]:
    course_dir = Path(course_dir)
    index_path = course_dir / "course_index.json"

    if not index_path.exists():
        raise FileNotFoundError(f"course_index.json not found in {course_dir}.")

    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    total_pages = index["total_pages"]
    mode = f"fixed {seconds_per_slide}s/slide" if seconds_per_slide is not None else "auto (per-page, based on content)"
    print(f"[Narrator] Course with {total_pages} pages | {mode} | Model: {model}\n")

    results = []
    for page_info in index["pages"]:
        json_path = Path(page_info["json_path"])
        result = narrate_page(
            json_path,
            seconds_per_slide=seconds_per_slide,
            model=model,
            api_key=api_key,
        )
        results.append(result)
        if "narration_text" in result:
            print(f"  -> {result['word_count']} words | ~{result['estimated_seconds']}s\n")

    full_narration_path = course_dir / "course_narration.json"
    with open(full_narration_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_estimated = sum(r.get("estimated_seconds", 0) for r in results)
    print(f"\n[Done] Full narration saved: {full_narration_path}")
    print(f"  Estimated total duration: {total_estimated / 60:.1f} minutes")

    return results

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate course narration from page JSON files")
    parser.add_argument("input", help="Path to page_XXXX.json or a directory with course_index.json")
    parser.add_argument("--seconds", "-s", type=int, default=None,
                        help="Force a fixed seconds/slide for all pages (default: auto, computed per page from content)")
    parser.add_argument("--model", "-m", type=str, default=DEFAULT_MODEL,
                        help=f"Groq model (default: {DEFAULT_MODEL})")
    parser.add_argument("--api-key", type=str, default=None)

    args = parser.parse_args()
    input_path = Path(args.input)

    if input_path.is_dir():
        narrate_course(input_path, seconds_per_slide=args.seconds,
                       model=args.model, api_key=args.api_key)
    elif input_path.suffix == ".json":
        result = narrate_page(input_path, seconds_per_slide=args.seconds,
                              model=args.model, api_key=args.api_key)
        print("\n" + "=" * 60)
        print("GENERATED NARRATION:")
        print("=" * 60)
        print(result["narration_text"])
        print("=" * 60)
        print(f"Words: {result['word_count']} | Estimated: {result['estimated_seconds']}s")
    else:
        print("Error: input must be a .json file or a directory")
        sys.exit(1)