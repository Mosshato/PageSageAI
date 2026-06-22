import json
import threading
from pathlib import Path

from django.conf import settings
from google import genai
from google.genai import types

from .constants import QUIZ_QUESTION_COUNT, QUIZ_OPTION_COUNT

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MAX_NARRATION_CHARS = 40_000


def collect_narration_text(ai_course) -> str:
    """Read all page_XXXX_narration.json files and return combined narration text."""
    output_dir = Path(ai_course.output_dir)
    parts = []
    for page_num in range(1, ai_course.total_pages + 1):
        narration_path = output_dir / f"page_{page_num:04d}_narration.json"
        if not narration_path.exists():
            continue
        try:
            with open(narration_path, encoding="utf-8") as f:
                data = json.load(f)
            text = data.get("narration_text", "").strip()
            if text:
                parts.append(f"[Page {page_num}]\n{text}")
        except Exception:
            continue

    combined = "\n\n".join(parts)
    if len(combined) > MAX_NARRATION_CHARS:
        combined = combined[:MAX_NARRATION_CHARS]
    return combined


def generate_quiz(quiz_id: int):
    from .models import Quiz

    quiz = Quiz.objects.select_related("ai_course").get(id=quiz_id)

    print(f"[Quiz Pipeline] Quiz {quiz_id} — started for course '{quiz.ai_course.title}'", flush=True)

    try:
        quiz.status = "GENERATING"
        quiz.save()

        narration_text = collect_narration_text(quiz.ai_course)
        if not narration_text.strip():
            raise ValueError("No narration text could be collected for this course.")

        print(f"[Quiz Pipeline] Quiz {quiz_id} — collected {len(narration_text)} chars of narration", flush=True)

        prompt = f"""You are an expert educator creating a quiz.
Based on the lecture content below, generate exactly {QUIZ_QUESTION_COUNT} multiple-choice questions
that test understanding of the key concepts.

Return ONLY a valid JSON array — no markdown fences, no preamble, no explanation.
Each element of the array must have exactly this structure:
{{
  "question": "The question text here?",
  "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
  "correct_index": 0
}}

Rules:
- correct_index is 0-based (0 = first option, {QUIZ_OPTION_COUNT - 1} = last option).
- All {QUIZ_OPTION_COUNT} options must be plausible; only one is correct.
- Questions must be specific to the lecture content, not generic.
- Do not number the questions.
- Output the JSON array and nothing else.

Lecture content:
{narration_text}
"""

        print(f"[Quiz Pipeline] Quiz {quiz_id} — calling Gemini...", flush=True)
        response = client.models.generate_content(
            model=settings.QUIZ_LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=settings.QUIZ_LLM_TEMPERATURE),
        )

        raw = response.text.strip()

        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        questions = json.loads(raw)

        if not isinstance(questions, list) or len(questions) < 10:
            raise ValueError(
                f"Gemini returned {len(questions) if isinstance(questions, list) else 'non-list'} "
                f"questions, expected {QUIZ_QUESTION_COUNT}."
            )

        questions = questions[:QUIZ_QUESTION_COUNT]

        for i, q in enumerate(questions):
            if not isinstance(q.get("options"), list) or len(q["options"]) != QUIZ_OPTION_COUNT:
                raise ValueError(f"Question {i} does not have exactly {QUIZ_OPTION_COUNT} options.")
            if not isinstance(q.get("correct_index"), int) or q["correct_index"] not in range(QUIZ_OPTION_COUNT):
                raise ValueError(f"Question {i} has invalid correct_index.")

        quiz.questions = questions
        quiz.status = "READY"
        quiz.error_msg = ""
        quiz.save()
        print(f"[Quiz Pipeline] Quiz {quiz_id} — READY ({len(questions)} questions)", flush=True)

    except Exception as e:
        quiz.status = "ERROR"
        quiz.error_msg = str(e)[:1000]
        quiz.save()
        print(f"[Quiz Pipeline] Quiz {quiz_id} — ERROR: {e}", flush=True)


def run_quiz_generation_in_background(quiz_id: int):
    thread = threading.Thread(target=generate_quiz, args=(quiz_id,), daemon=True)
    thread.start()
