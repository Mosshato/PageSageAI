# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered educational platform (Bachelor's thesis). Two components:

1. **FullstackApp** — Main web app: Django REST API + React/Vite frontend
2. **Functionalities** — Standalone utilities: PDF extraction, TTS narration, RAG pipeline

Teachers create classes, post assignments, upload PDFs. Students enroll, submit work, generate AI Manim animations, and take AI-generated quizzes.

---

## FullstackApp — Backend (Django)

**Location:** `FullstackApp/Backend/`
**Python venv:** `FullstackApp/Backend/venv/`
**Database:** PostgreSQL. Settings are split by environment (see Settings below) and read secrets from `FullstackApp/Backend/.env` — copy `.env.example` → `.env` and populate `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `GEMINI_API_KEY`, `GEMINI_API_KEY_MANIM`, `DEEPGRAM_API_KEY`, `GROQ_API_KEY`.

### Commands

```bash
# Activate venv (Windows)
cd FullstackApp/Backend && venv\Scripts\activate

# Run dev server
python manage.py runserver
# Add --noreload to suppress the double RuntimeWarning from StatReloader

# Migrations
python manage.py makemigrations
python manage.py migrate

# Seed database with demo data (creates teacher + student + 4 classes)
python manage.py seed
# Demo credentials: teacher@pagesageai.com / test1234  |  student@demo.com / test1234
# Demo class code for enrollment: DEMO01

# Tests
python manage.py test api
# Run a single test: python manage.py test api.tests.MyTestClass.test_method
```

### Settings (`core/settings/`)

Settings are a package, not a single file: `base.py` holds env-independent config (installed apps, JWT lifetimes, AI model names/params, `FUNCTIONALITIES_ROOT`/`OSSU_CHROMA_DIR`), `local.py` and `production.py` each do `from .base import *` and add what differs (secrets, `DATABASES`, `CORS_ALLOWED_ORIGINS`). `__init__.py` picks `production` if `ENV_NAME=production` else `local`. AI API keys (`GEMINI_API_KEY`, `GEMINI_API_KEY_MANIM`, `DEEPGRAM_API_KEY`) are read from `.env` via `local.py`/`production.py` — not hardcoded in pipeline files.

### Architecture

- `core/` — settings package + URL root (`/api/auth/` → `apps.authentication.urls`, `/api/` → `api.urls`, `/admin/`)
- `apps/authentication/` — standalone Django app: signup/login/me views, JWT issuing (`tokens_for_user`), `User` payload shaping. Registered in `INSTALLED_APPS` separately from `api`. Note: the `User` model lives in `api/models/auth.py` (registered as `AUTH_USER_MODEL = 'api.User'`); `apps/authentication/models.py` is empty — the auth app uses `get_user_model()` to reference it.
- `api/models/` — package, one module per domain: `auth.py` (`User`, `UserManager`), `classroom.py` (`Class`, `Enrollment`, `Announcement`), `assignment.py` (`Assignment`, `AssignmentAttachment`, `Submission`, `SubmissionFile`), `lecture.py` (`Lecture`, `LectureFile`), `ai.py` (`AICourse`, `ConceptAnimation`, `Quiz`, `QuizAttempt`). All re-exported from `api/models/__init__.py`.
- `api/views/` — package, one module per role/domain: `auth_views.py` (thin re-export of `apps.authentication.views`, kept so `api.views.auth_views` imports don't break), `student_views.py`, `teacher_views.py`, `ai_views.py` (AI courses, animations, quiz). All re-exported from `api/views/__init__.py`; `api/urls.py` imports the package as `views` and calls `views.<name>` — when adding an endpoint, add the function to the right module **and** export it from `api/views/__init__.py`.
- `api/services/` — background pipelines, one module each: `ai_pipeline.py` (AICourse pipeline + RAG), `manim_pipeline.py` (ConceptAnimation), `quiz_pipeline.py` (Quiz generation). Same add-and-export pattern isn't needed here since they're imported directly by module path.
- `api/serializers.py` — DRF serializers (student-facing vs teacher-facing variants)
- `api/constants.py` — fixed business rules shared across views/services (quiz question/option counts, grade bounds, class code length, Manim render timeout). Don't confuse with settings — constants here never come from `.env` and are identical across environments.
- `api/urls.py` — routes for everything except auth (`/api/`); `core/urls.py` mounts `apps.authentication.urls` at `/api/auth/` separately.
- `api/apps.py` — `ApiConfig.ready()` resumes any `PROCESSING` AICourses on startup

**Auth:** JWT via `djangorestframework-simplejwt`, issued by `apps/authentication/views.py`. Access tokens: 5 min; refresh tokens: 1 day. Token payload includes `role` and `firstName`. Frontend sends `Authorization: Bearer <token>`. `TokenRefreshView` (generic simplejwt, not auth-app-specific) is still wired in `api/urls.py` at `auth/token/refresh/`. Login requires `role` in the request body and rejects if it doesn't match the stored role (a student can't log in with `role=teacher`).

**Role separation:** Student endpoints: `/api/classes/`, `/api/assignments/`. Teacher endpoints: `/api/teacher/`. Views check `request.user` ownership manually — no DRF permission classes beyond `IsAuthenticated`.

**File uploads:** `Backend/media/` — submissions → `submissions/`, attachments → `attachments/`, AI course output → `ai_courses/<id>/`, animation scripts/videos → `animations/anim_<id>/`.

**CORS:** Only `http://localhost:5173` allowed (set in `core/settings/local.py`).

### Models

- `User` — email-based auth, `role=student|teacher`
- `Class(name, teacher_name, teacher FK, code, color, icon)` — `code` is a 6-char auto-generated enrollment key (`generate_code()` in `classroom.py`)
- `Enrollment(class_obj FK, student_email CharField, student_name CharField)` — student info stored as plain strings, **not** FK to `User`; no referential integrity with the auth table
- `Announcement`, `Assignment`, `AssignmentAttachment`, `Lecture`, `LectureFile`, `Submission`, `SubmissionFile` — standard academic models
- `AICourse(class_obj, title, filename, status, current_step, total_pages, error_msg, output_dir)` — status: `PROCESSING → READY | ERROR`; step: `PENDING → EXTRACTING → NARRATING → TTS → CHROMA → DONE`
- `ConceptAnimation(ai_course, concept, concept_key, status, video_file, retry_count, error_msg)` — status: `PENDING → GENERATING → RENDERING → READY | ERROR`; `unique_together = (ai_course, concept_key)`
- `Quiz(ai_course, status, questions JSONField, error_msg)` — `OneToOneField` to `AICourse`; status: `PENDING → GENERATING → READY | ERROR`; questions is a list of `{question, options[4], correct_index}`
- `QuizAttempt(quiz, student, answers JSONField, score, correct_count)` — one attempt per student per quiz

**`Assignment.status`** is intentionally denormalized — reflects the last student action across all students, not per-student state. Resubmission resets `graded → submitted`; unsubmit resets to `pending`.

---

## FullstackApp — Frontend (React)

**Location:** `FullstackApp/Frontend/frontend-app/`

### Commands

```bash
cd FullstackApp/Frontend/frontend-app
npm run dev       # dev server at http://localhost:5173
npm run lint
npm run build
```

No test runner is configured — the project has no frontend tests.

### Architecture

- `src/main.jsx` — Entry point: `AuthProvider` + `BrowserRouter`
- `src/context/AuthContext.jsx` — Global auth state; token in `localStorage`; role-based redirect after login
- `src/components/ProtectedRoute.jsx` — Route guard
- `src/pages/` — Public: `Welcome`, `Login`, `SignUp`
- `src/student/` — Student pages under `StudentLayout` (shared sidebar via `<Outlet>`): `StudentDashboard`, `StudentClasses`, `ClassDashboard`, `StudentAssignments`, `StudentCalendar`, `StudentAccount`, `AITeachDashboard`
- `src/teacher/` — Teacher pages (flat routes, no shared layout): `TeacherDashboard`, `TeacherClasses`, `TeacherClassDashboard`, `TeacherStudents`, `TeacherAccount`

**Key routing notes:**
- `AITeachDashboard` lives at `/student/ai-teach/:courseId` and is intentionally outside the `StudentLayout` route — it has **no sidebar**
- `StudentLectures` is a tab inside `ClassDashboard`, not a standalone route in `App.jsx`
- `AssignmentsContext` caches student assignments to avoid refetching across pages
- All API calls go to `http://localhost:8000/api/` with `Authorization: Bearer` attached manually per fetch
- All user-facing text is in English

---

## AI Features (Backend Pipelines)

### AICourse Pipeline (`api/services/ai_pipeline.py`)

Teacher uploads PDF → daemon thread runs 4 idempotent steps → students browse narrated pages + ask RAG questions.

| Step | Output | Done when |
|------|--------|-----------|
| EXTRACTING | PNGs + JSONs via `ingest_pdf` | `course_index.json` exists, page count matches PDF, all `page_XXXX.png` present |
| NARRATING | narration JSONs via `narrate_course` | all `page_XXXX_narration.json` present |
| TTS | MP3s via `generate_audio_for_course` | all `audio/page_XXXX.mp3` present and valid size |
| CHROMA | chunks added to shared ChromaDB | `chroma_indexed.marker` exists |

File naming: `page_0001.png`, `page_0001_narration.json`, `audio/page_0001.mp3`.

**RAG:** `query_rag()` uses the shared OSSU ChromaDB at `Functionalities/RAG/chroma_ossu_db/` (path centralized as `settings.OSSU_CHROMA_DIR`) with `settings.RAG_LLM_MODEL`. Course content coexists with OSSU content; chunks are prefixed `[Course {id} | Page {n}]`. The ChromaDB must be seeded first by running `Functionalities/RAG/createDB.py` before RAG queries work.

**Resume on restart:** `ApiConfig.ready()` in `api/apps.py` resumes all `PROCESSING` AICourses. The double RuntimeWarning from StatReloader is expected and harmless.

Console format: `[AI Pipeline] Course {id} — Step N: ...`

### ConceptAnimation Pipeline (`api/services/manim_pipeline.py`)

Student requests an animation → daemon thread, up to `MAX_RETRIES = 3`:
1. **GENERATING** — Gemini (`settings.GEMINI_API_KEY_MANIM`, `settings.MANIM_LLM_MODEL`) generates Manim code using `prompt_universal`; strips markdown fences
2. Writes `scene.py` to `media/animations/anim_{id}/`
3. **RENDERING** — `manim -ql --media_dir <work_dir> scene.py ConceptScene` (subprocess, timeout from `constants.MANIM_RENDER_TIMEOUT_SECONDS`)
4. Finds `.mp4`, saves path, marks `READY`

Scene class must be named `ConceptScene`. `manim` CLI must be on PATH in the Django venv.

Caching: `concept_key = concept.strip().lower()`. Existing `READY` animation for same `(ai_course, concept_key)` is returned immediately.

Console format: `[Manim Pipeline] Animation {id} — ...`

### Quiz Pipeline (`api/services/quiz_pipeline.py`)

Teacher triggers quiz generation for an AICourse → daemon thread:
1. Collects all `page_XXXX_narration.json` text (max 40,000 chars)
2. Calls Gemini (`settings.GEMINI_API_KEY`, `settings.QUIZ_LLM_MODEL`) to produce exactly `constants.QUIZ_QUESTION_COUNT` MCQs as a JSON array
3. Validates structure (`constants.QUIZ_OPTION_COUNT` options, valid `correct_index`), saves to `Quiz.questions`, marks `READY`

`Quiz` is `OneToOneField` to `AICourse`. Students submit attempts via `QuizAttempt`; score is computed server-side. Teacher can view per-student results.

Console format: `[Quiz Pipeline] Quiz {id} — ...`

### API Endpoints

**Misc:**
- `GET api/ping/` — health check (defined in `core/urls.py` + `core/views.py`)

**Auth (mounted at `/api/auth/`, defined in `apps/authentication/urls.py`):**
- `POST signup/`, `POST login/`, `GET me/`

**Everything else (mounted at `/api/`, defined in `api/urls.py`):**

Student — Classes & Assignments:
- `GET classes/` — list enrolled classes
- `POST classes/enroll/` — enroll by code
- `GET classes/<id>/` — class detail (announcements, assignments, lectures)
- `DELETE classes/<id>/quit/` — quit class
- `GET assignments/` — all student assignments across classes
- `POST assignments/<id>/submit/` — submit or resubmit
- `DELETE assignments/<id>/unsubmit/` — retract submission
- `GET account/stats/` — student stats

Teacher:
- `GET/POST teacher/classes/` — list / create class
- `GET teacher/classes/<id>/` — class detail with enrollments and submissions
- `POST/DELETE teacher/classes/<id>/students/` / `teacher/classes/<id>/students/<enrollment_id>/` — add/remove student
- `POST teacher/classes/<id>/announcements/` / `DELETE .../announcements/<id>/` — announcements
- `POST teacher/classes/<id>/assignments/` / `DELETE .../assignments/<id>/` / `PUT .../assignments/<id>/edit/` — assignments
- `POST teacher/classes/<id>/lectures/` / `DELETE .../lectures/<id>/` — lectures
- `POST teacher/classes/<id>/submissions/<id>/grade/` — grade a submission
- `GET teacher/stats/`, `GET teacher/students/`

AI Teaching:
- `POST teacher/classes/<id>/ai-courses/` — upload PDF
- `DELETE teacher/classes/<id>/ai-courses/<id>/` — delete course
- `GET ai-courses/class/<id>/` — list courses
- `GET ai-courses/<id>/status/` — poll pipeline status
- `GET ai-courses/<id>/page/<n>/` — image + audio URL for page n
- `POST ai-courses/<id>/ask/` — RAG question
- `POST ai-courses/<id>/reformulate/` — simplified re-explanation

Animations:
- `POST ai-courses/<id>/animations/` — request animation (returns `animation_id`, `status`, `cached`)
- `GET ai-courses/<id>/animations/list/` — library
- `GET animations/<id>/status/` — poll; returns `video_url` when READY

Quiz:
- `POST teacher/classes/<id>/ai-courses/<id>/generate-quiz/` — trigger generation
- `GET teacher/classes/<id>/ai-courses/<id>/quiz-results/` — per-student results
- `GET ai-courses/<id>/quiz/status/` — poll status
- `GET ai-courses/<id>/quiz/questions/` — fetch questions (students)
- `POST ai-courses/<id>/quiz/attempt/` — submit answers

### Frontend AI Pages

- `AITeachDashboard.jsx` — tabs: **◉ Lecture** (audio player + RAG chat + ⊕ Animate button) and **⬡ Animations** (library with status badges, inline video player)
- Animations poll every 4 seconds; on READY switches to Animations tab
- `TeacherClassDashboard.jsx` — drag-zone for PDF upload; collapses to compact button when courses exist

---

## Functionalities

**Location:** `Functionalities/`
**Python venv:** `Functionalities/venv/`
**Env vars:** `Functionalities/.env` (Claude/OpenAI API keys)

- `PDFExtraction/textAndImageExtraction.py` (`ingest_pdf`) — PDF → per-page PNGs + JSONs + `course_index.json`
- `PDFExtraction/tableExtraction.py` (`narrate_course`) — JSONs → narration JSONs (per-page resume built in)
- `PDFExtraction/TTS.py` (`generate_audio_for_course`) — narration JSONs → MP3s (per-page resume built in)
- `RAG/createDB.py` — seeds ChromaDB at `chroma_ossu_db/` from OSSU curriculum markdown; **must be run once before RAG queries work**
- `RAG/testRAG.py` — query the RAG pipeline manually
- `RAG/verifica_db.py` — inspect ChromaDB contents

## Cross-Cutting Notes

- **Python 3.11** throughout; each subdirectory has its own venv — activate the correct one
- **No shared `requirements.txt` at root** — backend deps are in `FullstackApp/Backend/venv/`
- **Manim rendering** uses `-ql` (low quality, no preview window) server-side; scene class must be `ConceptScene`
- Some backend code comments are in Romanian (the author's native language) — this is intentional, not stale, and not limited to a single module
