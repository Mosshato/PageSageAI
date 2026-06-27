"""
Constante de domeniu folosite in mai multe fisiere din api/.
Scop: elimina "magic numbers" repetate (DRY) — daca o valoare se schimba,
se schimba intr-un singur loc, nu se cauta prin toate view-urile/pipeline-urile.

"""

# ── Quiz ───────────────────────────────────────────────────────────────────
QUIZ_QUESTION_COUNT = 20      # numarul de intrebari generate per quiz
QUIZ_OPTION_COUNT = 4         # numarul de variante per intrebare (A-D)

# ── Notare (Submission.grade / Assignment.grade) ────────────────────────────
MIN_GRADE = 0
MAX_GRADE = 100

# ── Class.code (codul de inscriere generat automat) ─────────────────────────
CLASS_CODE_LENGTH = 6

# ── Manim (randare animatii) ────────────────────────────────────────────────
MANIM_RENDER_TIMEOUT_SECONDS = 180
MANIM_MAX_RETRIES = 3

# ── Narration (generare naratie per pagina) ──────────────────────────────────
NARRATION_WORDS_PER_MINUTE = 130
NARRATION_MIN_SECONDS_PER_SLIDE = 20
NARRATION_MAX_SECONDS_PER_SLIDE = 110

# ── TTS / Deepgram ────────────────────────────────────────────────────────────
TTS_RATE_LIMIT_DELAY = 6.5    # secunde intre requesturi (limita free tier Deepgram)
TTS_MAX_RETRIES = 5
