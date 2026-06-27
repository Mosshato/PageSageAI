import os
import subprocess
import threading

from django.conf import settings
from google import genai
from google.genai import types

from ..constants import MANIM_RENDER_TIMEOUT_SECONDS, MANIM_MAX_RETRIES as MAX_RETRIES

client = genai.Client(api_key=settings.GEMINI_API_KEY_MANIM)


def _build_prompt(concept):
    prompt_universal = f"""#
You are an expert Manim animator and Python engineer specializing in **Manim Community Edition (ManimCE), modern API v0.18+**. Produce a single, self-contained, error-free Manim script that creates a **~30-second educational animation** explaining the concept: **{concept}**.

## HARD REQUIREMENTS
- Output **ONLY valid Python code**. No markdown fences, no commentary, no text before or after the code.
- Target **Manim Community Edition only**. Start the file with `from manim import *`. Never use ManimGL-only syntax (no `ShowCreation`, no `from manimlib import *`).
- Define **exactly ONE** `Scene` subclass named `ConceptScene` with a `construct(self)` method. All animation logic lives inside it. Module-level helper functions are allowed.
- The file must run **as-is** via `manim -pqh file.py ConceptScene` with **no external assets** (no image/font/sound files), **no network calls**, and **no extra pip packages** beyond `manim` (note: `np` is already available through the manim import).
- Do not name variables/classes in a way that shadows manim built-ins (e.g. don't name a variable `Text`, `Line`, `config`).

## DURATION (target 28–32 seconds)
- Track time explicitly: every `self.play(..., run_time=t)` adds `t` seconds (default `1.0` if unset); every `self.wait(t)` adds `t`. Sum them and land in 28–32s.
- Suggested structure: **title/intro (~4s) → setup the scene (~5s) → core step-by-step demonstration (~16s) → recap/takeaway (~5s)**.

## ANIMATION API — USE ONLY STABLE, KNOWN-GOOD CALLS
- Creation/removal: `Create`, `Write`, `FadeIn`, `FadeOut`, `DrawBorderThenFill`, `GrowFromCenter`, `Uncreate`.
- Transforms & emphasis: `Transform`, `ReplacementTransform`, `TransformMatchingTex`, the `.animate` syntax (e.g. `self.play(mob.animate.shift(RIGHT).set_color(YELLOW))`), `Indicate`, `Flash`, `Circumscribe`, `FocusOn`, `Wiggle`.
- Positioning helpers: `.move_to`, `.next_to`, `.shift`, `.to_edge`, `.to_corner`, `.align_to`, `.scale`, `.arrange`, `.arrange_in_grid` (always use a `buff=` to space items).
- Grouping: `VGroup`, `Group`. Prefer `VGroup(...).arrange(RIGHT, buff=0.3)` to lay out rows/columns cleanly.
- Optional (only if it helps): `ValueTracker` + `add_updater` for smooth numeric/positional animation — but **remove all updaters** (`mob.clear_updaters()`) before the scene ends.
- Colors: use **built-in constants only** — `WHITE, BLACK, GREY, BLUE, TEAL, GREEN, YELLOW, GOLD, ORANGE, RED, MAROON, PURPLE, PINK` and their `_A/_B/_C/_D/_E` variants. For custom colors use hex strings like `"#1f77b4"`. Never invent color names.

## TEXT & MATH (avoid LaTeX failures)
- Prefer `Text("...")` for all labels and prose — it has **no LaTeX dependency**.
- Use `MathTex(...)` **only** for genuine math, keep expressions short and valid, and always use **raw strings** for backslashes: `MathTex(r"\frac{{a}}{{b}}")`. Keep MathTex objects to a minimum.
- Never put plain non-math words inside `MathTex`.

## LAYOUT — NO OVERLAPS, NOTHING OFF-SCREEN
- The visible frame is ~14.2 wide × 8 tall, centered at `ORIGIN`. Keep every object roughly within `x ∈ [-7, 7]`, `y ∈ [-4, 4]`.
- Title → `.to_edge(UP)`; captions/explanations → `.to_edge(DOWN)`. Reserve the center for the main visual.
- Plan positions before adding many elements; use `.arrange`, `buff=`, and `.next_to` to prevent overlap.
- `FadeOut` or move away elements you no longer need so the screen never gets cluttered. To clear everything, use `self.play(FadeOut(*self.mobjects))`.
- If a group is too big, `.scale(...)` it down so it fits within the frame.

## PEDAGOGY
- Actually **teach {concept}**: show the key idea visually, step through the mechanism, and label what is happening at each step.
- Use color changes and motion (`Indicate`, recoloring) to highlight the *active* element at each step.
- Finish with a single clear one-line takeaway.

## SELF-CHECK (do this silently, then output only the code)
- [ ] Every mobject is created/added before it is referenced or transformed.
- [ ] No deprecated or ManimGL-only method is used.
- [ ] All `MathTex` strings are valid LaTeX and written as raw strings.
- [ ] Estimated total `run_time` + `wait` is 28–32s.
- [ ] No object leaves the frame; no two important objects overlap unintentionally.
- [ ] The file is complete, top-to-bottom runnable, and contains only Python.

Now write the complete Manim script for: **{concept}**
"""
    return prompt_universal


def generate_and_render_animation(animation_id: int):
    from ..domain import ConceptAnimation

    animation = ConceptAnimation.objects.get(id=animation_id)
    concept = animation.concept

    print(f"[Manim Pipeline] Animation {animation_id} — started | concept='{concept}'", flush=True)

    for attempt in range(MAX_RETRIES):
        try:
            print(f"[Manim Pipeline] Animation {animation_id} — attempt {attempt + 1}/{MAX_RETRIES}", flush=True)

            # --- STEP 1: Generate Manim code ---
            animation.status = 'GENERATING'
            animation.save()
            print(f"[Manim Pipeline] Animation {animation_id} — Step 1: generating Manim code via Gemini...", flush=True)

            prompt = _build_prompt(concept)
            response = client.models.generate_content(
                model=settings.MANIM_LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=settings.MANIM_LLM_TEMPERATURE),
            )
            raw = response.text.strip()

            if raw.startswith("```python"):
                raw = raw[9:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            code = raw.strip()
            print(f"[Manim Pipeline] Animation {animation_id} — Step 1: done ({len(code)} chars)", flush=True)

            # --- STEP 2: Write script to disk ---
            work_dir = os.path.join(settings.MEDIA_ROOT, 'animations', f'anim_{animation_id}')
            os.makedirs(work_dir, exist_ok=True)
            script_path = os.path.join(work_dir, 'scene.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"[Manim Pipeline] Animation {animation_id} — Step 2: script written to {script_path}", flush=True)

            # --- STEP 3: Render with Manim ---
            animation.status = 'RENDERING'
            animation.save()
            print(f"[Manim Pipeline] Animation {animation_id} — Step 3: rendering with Manim...", flush=True)

            result = subprocess.run(
                ['manim', '-ql', '--media_dir', work_dir, 'scene.py', 'ConceptScene'],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=MANIM_RENDER_TIMEOUT_SECONDS,
            )
            if result.returncode != 0:
                err = result.stderr[-2000:] if result.stderr else "Manim exited with error"
                print(f"[Manim Pipeline] Animation {animation_id} — Step 3: FAILED\n{err}", flush=True)
                raise RuntimeError(err)
            print(f"[Manim Pipeline] Animation {animation_id} — Step 3: render complete", flush=True)

            # --- STEP 4: Find the output .mp4 ---
            video_path = None
            for root, dirs, files in os.walk(work_dir):
                for f in files:
                    if f.endswith('.mp4'):
                        video_path = os.path.join(root, f)
                        break
                if video_path:
                    break
            if not video_path:
                raise FileNotFoundError("Manim produced no .mp4 output")
            print(f"[Manim Pipeline] Animation {animation_id} — Step 4: video found at {video_path}", flush=True)

            # --- STEP 5: Save and mark READY ---
            relative = os.path.relpath(video_path, settings.MEDIA_ROOT)
            animation.video_file = relative
            animation.status = 'READY'
            animation.save()
            print(f"[Manim Pipeline] Animation {animation_id} — READY", flush=True)
            return

        except Exception as e:
            animation.retry_count = attempt + 1
            animation.save()
            print(f"[Manim Pipeline] Animation {animation_id} — attempt {attempt + 1} failed: {e}", flush=True)
            if attempt == MAX_RETRIES - 1:
                animation.status = 'ERROR'
                animation.error_msg = "Animation could not be generated, please try again later."
                animation.save()
                print(f"[Manim Pipeline] Animation {animation_id} — ERROR after {MAX_RETRIES} attempts", flush=True)
                return


def run_animation_in_background(animation_id: int):
    thread = threading.Thread(
        target=generate_and_render_animation,
        args=(animation_id,),
        daemon=True,
    )
    thread.start()
