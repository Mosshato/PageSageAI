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
