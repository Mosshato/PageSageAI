"""
TTS Generator — Deepgram Aura-2
--------------------------------
Parcurge un director cu *_narration.json si genereaza cate un fisier .mp3 pentru fiecare pagina.

Features:
  - Resume automat: sare peste paginile deja generate corect
  - Retry cu backoff exponential pentru erori de retea si rate limit
  - Sterge fisierele partiale inainte de retry

Dependencies:
    pip install requests
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from django.conf import settings

from ..constants import (
    TTS_RATE_LIMIT_DELAY as RATE_LIMIT_DELAY,
    TTS_MAX_RETRIES as MAX_RETRIES,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

DEFAULT_VOICE = settings.TTS_VOICE

OUTPUT_FORMAT = "mp3"
SAMPLE_RATE   = 24000

MIN_VALID_SIZE_BYTES = 1024

RETRY_BASE_DELAY = 5.0

# ---------------------------------------------------------------------------
# Single TTS request cu retry
# ---------------------------------------------------------------------------

def text_to_speech(
    text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE,
    api_key: str = "",
) -> bool:
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

            if response.status_code == 429:
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"    [429 Rate limit] Attempt {attempt}/{MAX_RETRIES}. "
                      f"Waiting {wait:.0f}s...")
                time.sleep(wait)
                continue

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

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)

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
            if output_path.exists():
                output_path.unlink()

            wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"    [Network error] {type(e).__name__}: {str(e)[:80]}")
            print(f"    Retry in {wait:.0f}s... ({attempt}/{MAX_RETRIES})")
            time.sleep(wait)
            continue

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
    narration_json_path = Path(narration_json_path)

    with open(narration_json_path, encoding="utf-8") as f:
        data = json.load(f)

    text        = data.get("narration_text", "").strip()
    page_number = data.get("page_number", "?")

    if not text:
        print(f"  [Skip] Page {page_number} — narration_text gol")
        return None

    MAX_CHARS = 1900
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(" ", 1)[0]
        print(f"  [Warn] Page {page_number} — text trunchiat la {len(text)} chars (limita Deepgram)")

    base_name   = narration_json_path.name.replace("_narration.json", "")
    audio_dir   = narration_json_path.parent / audio_subdir
    audio_dir.mkdir(exist_ok=True)
    output_path = audio_dir / f"{base_name}.{OUTPUT_FORMAT}"

    if output_path.exists() and output_path.stat().st_size >= MIN_VALID_SIZE_BYTES:
        size_kb = output_path.stat().st_size / 1024
        print(f"  [Skip] Page {page_number} — {output_path.name} exista ({size_kb:.1f} KB)")
        return output_path

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
        print("    Ruleaza mai intai narration.py")
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

        if i < total and audio_path and not was_existing:
            time.sleep(RATE_LIMIT_DELAY)

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
