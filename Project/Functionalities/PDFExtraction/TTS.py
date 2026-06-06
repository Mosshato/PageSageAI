"""
TTS Generator — Deepgram Aura-2
--------------------------------
Parcurge poze_output/, gaseste toate fisierele *_narration.json
si genereaza cate un fisier .mp3 pentru fiecare pagina.

Features:
  - Resume automat: sare peste paginile deja generate corect
  - Retry cu backoff exponential pentru erori de retea si rate limit
  - Sterge fisierele partiale inainte de retry

Dependencies:
    pip install requests python-dotenv

.env:
    DEEPGRAM_API_KEY=your_key_here

Usage:
    python tts_generator.py poze_output/
    python tts_generator.py poze_output/ --voice aura-2-zeus-en
    python tts_generator.py poze_output/page_0001_narration.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

DEFAULT_VOICE = "aura-2-orpheus-en"
# "aura-2-arcas-en"   — Natural, Smooth, Clear
# "aura-2-zeus-en"    — Deep, Trustworthy, Smooth
# "aura-2-hermes-en"  — Expressive, Engaging, Professional
# "aura-2-jupiter-en" — Expressive, Knowledgeable, Baritone

OUTPUT_FORMAT = "mp3"
SAMPLE_RATE   = 24000

# Minimum valid MP3 size — sub 1KB inseamna fisier corupt sau gol
MIN_VALID_SIZE_BYTES = 1024

# Delay intre requesturi (rate limit free tier ~10 req/min)
RATE_LIMIT_DELAY = 6.5

# Retry config
MAX_RETRIES = 5
RETRY_BASE_DELAY = 5.0   # secunde, se dubleaza la fiecare retry

# ---------------------------------------------------------------------------
# Single TTS request cu retry
# ---------------------------------------------------------------------------

def text_to_speech(
    text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE,
    api_key: str = "",
) -> bool:
    """
    Trimite textul la Deepgram si salveaza audio-ul la output_path.
    Retry automat pe erori de retea sau rate limit (429).
    Sterge fisierele partiale inainte de orice retry.
    Returneaza True daca a reusit, False dupa MAX_RETRIES esecuri.
    """
    key = api_key or DEEPGRAM_API_KEY
    if not key:
        raise ValueError(
            "DEEPGRAM_API_KEY nu e setat. "
            "Adauga in .env: DEEPGRAM_API_KEY=your_key"
        )

    params = {"model": voice, "encoding": OUTPUT_FORMAT}
    if OUTPUT_FORMAT.lower() != "mp3":
        params["sample_rate"] = SAMPLE_RATE
    headers = {"Authorization": f"Token {key}", "Content-Type": "application/json"}
    payload = {"text": text}

    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, MAX_RETRIES + 1):
        # Sterge orice fisier partial ramas de la un attempt anterior
        if output_path.exists():
            output_path.unlink()

        try:
            response = requests.post(
                DEEPGRAM_TTS_URL,
                params=params,
                headers=headers,
                json=payload,
                timeout=90,
                stream=True,
            )

            # Rate limit
            if response.status_code == 429:
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"    [429 Rate limit] Attempt {attempt}/{MAX_RETRIES}. "
                      f"Waiting {wait:.0f}s...")
                time.sleep(wait)
                continue

            # Alta eroare HTTP
            if response.status_code != 200:
                try:
                    err = response.json()
                except Exception:
                    err = response.text[:200]
                print(f"    [HTTP {response.status_code}] {err}")
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"    Retry in {wait:.0f}s... ({attempt}/{MAX_RETRIES})")
                time.sleep(wait)
                continue

            # Scrie audio in fisier chunk cu chunk
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)

            # Verifica ca fisierul nu e gol sau trunchiat
            if output_path.exists() and output_path.stat().st_size >= MIN_VALID_SIZE_BYTES:
                return True
            else:
                size = output_path.stat().st_size if output_path.exists() else 0
                print(f"    [Warn] Fisier prea mic ({size} bytes) — probabil trunchiat.")
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"    Retry in {wait:.0f}s... ({attempt}/{MAX_RETRIES})")
                time.sleep(wait)
                continue

        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
        ) as e:
            # Sterge fisierul partial daca exista
            if output_path.exists():
                output_path.unlink()

            wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"    [Network error] {type(e).__name__}: {str(e)[:80]}")
            print(f"    Retry in {wait:.0f}s... ({attempt}/{MAX_RETRIES})")
            time.sleep(wait)
            continue

    # Toate retry-urile au esuat
    if output_path.exists():
        output_path.unlink()
    print(f"    [FAIL] Abandonat dupa {MAX_RETRIES} incercari.")
    return False

# ---------------------------------------------------------------------------
# Process a single narration JSON
# ---------------------------------------------------------------------------

def generate_audio_for_page(
    narration_json_path: Path,
    voice: str = DEFAULT_VOICE,
    api_key: str = "",
    audio_subdir: str = "audio",
) -> Optional[Path]:
    """
    Citeste un *_narration.json, genereaza MP3 si il salveaza in audio/.
    Returneaza path-ul catre MP3 sau None daca a esuat.
    """
    narration_json_path = Path(narration_json_path)

    with open(narration_json_path, encoding="utf-8") as f:
        data = json.load(f)

    text        = data.get("narration_text", "").strip()
    page_number = data.get("page_number", "?")

    if not text:
        print(f"  [Skip] Page {page_number} — narration_text gol")
        return None

    # Deepgram free tier limit: 2000 chars — truncate la ultimul cuvânt complet
    MAX_CHARS = 1900
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(" ", 1)[0]
        print(f"  [Warn] Page {page_number} — text trunchiat la {len(text)} chars (limita Deepgram)")

    base_name   = narration_json_path.name.replace("_narration.json", "")
    audio_dir   = narration_json_path.parent / audio_subdir
    audio_dir.mkdir(exist_ok=True)
    output_path = audio_dir / f"{base_name}.{OUTPUT_FORMAT}"

    # Resume: skip daca fisierul audio exista si e valid (nu trunchiat)
    if output_path.exists() and output_path.stat().st_size >= MIN_VALID_SIZE_BYTES:
        size_kb = output_path.stat().st_size / 1024
        print(f"  [Skip] Page {page_number} — {output_path.name} exista ({size_kb:.1f} KB)")
        return output_path

    # Daca exista dar e prea mic (trunchiat), sterge-l si refă
    if output_path.exists():
        print(f"  [Warn] Page {page_number} — fisier partial detectat, il sterg si refac")
        output_path.unlink()

    print(f"  [TTS] Page {page_number} | {len(text.split())} words | Voice: {voice}")

    success = text_to_speech(text, output_path, voice=voice, api_key=api_key)

    if success:
        size_kb = output_path.stat().st_size / 1024
        print(f"  [OK] {output_path.name} ({size_kb:.1f} KB)")
        return output_path
    else:
        return None

# ---------------------------------------------------------------------------
# Process full course directory
# ---------------------------------------------------------------------------

def generate_audio_for_course(
    course_dir: Path,
    voice: str = DEFAULT_VOICE,
    api_key: str = "",
) -> list[dict]:
    course_dir = Path(course_dir)

    narration_files = sorted(
        [p for p in course_dir.glob("*_narration.json") 
        if p.name != "course_narration.json"],
        key=lambda p: p.name,
    )

    if not narration_files:
        print(f"[!] Nu am gasit fisiere *_narration.json in {course_dir}")
        print("    Ruleaza mai intai lecture_narrator.py")
        sys.exit(1)

    total = len(narration_files)
    print(f"[TTS] {total} pagini de procesat | Voice: {voice}")
    print(f"      Output: {course_dir / 'audio'}/\n")

    results  = []
    skipped  = 0
    success  = 0
    failed   = 0

    for i, narration_path in enumerate(narration_files, 1):
        print(f"[{i}/{total}] {narration_path.name}")

        was_existing = _audio_exists(narration_path, course_dir / "audio")

        audio_path = generate_audio_for_page(
            narration_path,
            voice=voice,
            api_key=api_key,
        )

        if audio_path:
            if was_existing:
                skipped += 1
            else:
                success += 1
        else:
            failed += 1

        results.append({
            "narration_json": str(narration_path),
            "audio_path": str(audio_path) if audio_path else None,
            "success": audio_path is not None,
        })

        # Delay intre requesturi reale (nu si dupa skip-uri)
        if i < total and audio_path and not was_existing:
            time.sleep(RATE_LIMIT_DELAY)

    # Salveaza manifest
    manifest_path = course_dir / "audio_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] {success} generate | {skipped} skipped | {failed} failed")
    print(f"  Audio dir: {course_dir / 'audio'}")
    print(f"  Manifest:  {manifest_path}")

    return results


def _audio_exists(narration_path: Path, audio_dir: Path) -> bool:
    base = narration_path.name.replace("_narration.json", "")
    p = audio_dir / f"{base}.{OUTPUT_FORMAT}"
    return p.exists() and p.stat().st_size >= MIN_VALID_SIZE_BYTES

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genereaza audio MP3 din fisierele _narration.json folosind Deepgram TTS"
    )
    parser.add_argument(
        "input",
        help="Director cu *_narration.json sau un singur fisier *_narration.json",
    )
    parser.add_argument(
        "--voice", "-v",
        default=DEFAULT_VOICE,
        help=f"Vocea Deepgram Aura-2 (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="Deepgram API key (sau seteaza DEEPGRAM_API_KEY in .env)",
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    if input_path.is_dir():
        generate_audio_for_course(input_path, voice=args.voice, api_key=args.api_key)
    elif input_path.is_file() and input_path.name.endswith("_narration.json"):
        result = generate_audio_for_page(input_path, voice=args.voice, api_key=args.api_key)
        if result:
            print(f"\nAudio generat: {result}")
    else:
        print("Eroare: input trebuie sa fie un director sau un fisier *_narration.json")
        sys.exit(1)