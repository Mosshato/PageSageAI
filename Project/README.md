# PageSage AI — AI-Powered Educational Platform

An educational platform that allows teachers to create classes, upload PDF lectures processed by AI (narration, audio, RAG Q&A), generate Manim animations and quizzes, while students can enroll, submit assignments, and learn interactively with AI.

---

## Table of Contents

- [User Guide](#user-guide)
  - [Teacher](#teacher)
  - [Student](#student)
- [Technical Setup](#technical-setup)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Environment Variables (.env)](#environment-variables-env)
  - [Third-Party Services](#third-party-services)
  - [Database Setup](#database-setup)
  - [Running the Application](#running-the-application)
  - [Configurable Constants](#configurable-constants)
  - [AI Model Settings](#ai-model-settings)

---

## User Guide

### Teacher

#### 1. Create an Account
- Go to `http://localhost:5173`
- Click **Sign Up**
- Fill in your name, email, password and select role **Teacher**
- Click **Create Account**

#### 2. Log In
- Click **Log In**, enter your email and password, select role **Teacher**

#### 3. Create a Class
- From the dashboard click **Create Class**
- Enter a class name — a unique 6-character enrollment code is auto-generated (e.g. `DEMO01`)
- Share this code with your students so they can enroll
- You can customize the class color and icon

#### 4. Manage a Class
Open a class to access all management tabs:

**Announcements**
- Click **New Announcement** to post a message visible to all enrolled students

**Assignments**
- Click **Add Assignment** → fill in title, description, due date
- Optionally attach files (PDFs, documents)
- After students submit, open each submission to read it and enter a grade (0–100)
- Click **Grade** to save — the student sees their grade immediately

**Lectures**
- Click **Add Lecture** → enter title and upload any supporting files
- Lectures are visible to all enrolled students

**Students**
- View all enrolled students
- Add a student manually by email or remove them from the class

#### 5. AI Teaching — Upload a PDF Course
- Inside a class, go to the **AI Teach** section
- Drag and drop a PDF lecture file or click to browse
- Enter a course title and click **Upload**
- The backend processes the PDF automatically through 4 stages:
  - **EXTRACTING** — PDF pages → PNG images + structured JSON
  - **NARRATING** — AI (Groq LLaMA) generates a spoken narration per page
  - **TTS** — Deepgram converts narration text to MP3 audio
  - **CHROMA** — content is indexed in ChromaDB for RAG queries
- A progress indicator shows the current step; when complete the course shows **READY**

#### 6. Generate a Quiz
- Open an AI course that is **READY**
- Click **Generate Quiz**
- Gemini AI reads all narrations and generates 20 multiple-choice questions (4 options each)
- Once generated, students can take the quiz; you can view per-student results from the **Quiz Results** tab

#### 7. View Statistics
- From the main dashboard click **Stats** to see total classes, students, assignments and submission rates

---

### Student

#### 1. Create an Account
- Go to `http://localhost:5173`
- Click **Sign Up**
- Fill in your name, email, password and select role **Student**

#### 2. Log In
- Click **Log In**, enter your email and password, select role **Student**

#### 3. Enroll in a Class
- From your dashboard click **Enroll in Class**
- Enter the 6-character code given by your teacher (e.g. `DEMO01`)
- The class appears immediately in your dashboard

#### 4. View Class Content
Inside a class you can browse:
- **Announcements** — messages posted by the teacher
- **Assignments** — tasks with due dates and attached files
- **Lectures** — lecture materials uploaded by the teacher
- **AI Course** — if the teacher uploaded a PDF, you can access the AI-processed course here

#### 5. Submit an Assignment
- Open an assignment and click **Submit**
- Upload your file(s) and confirm
- You can **Resubmit** (replaces previous submission) or **Unsubmit** (retract) at any time before grading
- Once graded, you see your score and any feedback

#### 6. Learn with AI — AI Course Viewer
- Open an AI course from your class → click **Launch AI Course**
- Use the **◉ Lecture** tab to browse narrated slides:
  - Each page shows the slide image with an audio player (MP3 narration)
  - Read along or listen to the AI professor explain the content

#### 7. Ask the AI (RAG Q&A)
- In the Lecture tab, type any question in the **Ask a question** box
- The RAG engine searches the course content + OSSU curriculum and answers in context
- If the answer is unclear, click **Explain differently** — the AI rephrases with simpler language and analogies

#### 8. Generate a Concept Animation
- While viewing a slide, click the **⊕ Animate** button next to any concept
- Type the concept you want animated (e.g. "bubble sort", "binary search tree")
- The backend generates a Manim Python animation and renders it as an MP4 video
- When ready (status turns **READY**), the video plays inline
- Already-generated animations are cached — the same concept won't be re-generated

#### 9. Take a Quiz
- If the teacher generated a quiz for the course, you see a **Take Quiz** button
- Answer all 20 multiple-choice questions and click **Submit**
- Your score and correct answers are shown immediately
- One attempt per student per quiz

#### 10. View Your Progress
- From the sidebar go to **Assignments** to see all tasks across all classes with their status (pending / submitted / graded)
- Go to **Account → Stats** to see your submission rate and grades summary
- The **Calendar** view shows upcoming assignment due dates

---

## Technical Setup

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11 | Strictly 3.11 — torch and transformers require it |
| Node.js | 18+ | For the React frontend |
| PostgreSQL | 14+ | Main database |
| Manim | Community Edition | Must be installed and on PATH |
| Git | Any | |

#### Install Manim (Community Edition)
Manim requires a separate system-level installation:
```bash
# Windows (with chocolatey)
choco install manim

# Or via pip inside the venv (after activating):
pip install manim

# Verify it works:
manim --version
```
Manim also requires **FFmpeg** and **LaTeX** (MiKTeX on Windows) to be on PATH for rendering.

---

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd FullstackApp/Backend

# 2. Create a Python 3.11 virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install all dependencies
pip install Django==5.2.14
pip install djangorestframework==3.17.1
pip install djangorestframework-simplejwt==5.5.1
pip install django-cors-headers==4.9.0
pip install psycopg2-binary==2.9.12
pip install python-dotenv==1.2.2
pip install PyMuPDF==1.27.2.3
pip install pillow==12.2.0
pip install torch==2.12.0
pip install transformers==5.9.0
pip install groq==1.2.0
pip install google-genai==1.75.0
pip install requests==2.34.2
pip install langchain-core==1.4.0
pip install langchain-text-splitters==1.1.2
pip install langchain-huggingface==1.2.2
pip install langchain-chroma==1.1.0
pip install langchain-google-genai==4.2.3
pip install chromadb==1.5.9
pip install sentence-transformers==5.5.1
pip install scikit-learn==1.8.0
pip install numpy==2.4.6
pip install locust==2.44.4
pip install matplotlib==3.11.0

# Alternatively, if a requirements.txt is available:
pip install -r requirements.txt
```

**Note on first run:** The `transformers` library will download the LayoutLMv3 model (~900MB) from HuggingFace on the first PDF processing request. This is automatic and cached locally after the first download. Similarly, the `sentence-transformers` embedding model (`all-MiniLM-L6-v2`) downloads once on first ChromaDB use.

---

### Frontend Setup

```bash
# Navigate to frontend directory
cd FullstackApp/Frontend/frontend-app

# Install dependencies
npm install

# Start development server
npm run dev
# Runs at http://localhost:5173
```

**Frontend dependencies (from package.json):**
- `react` ^19.2.5
- `react-dom` ^19.2.5
- `react-router-dom` ^7.15.0
- `vite` ^8.0.10 (dev server + bundler)

---

### Environment Variables (.env)

Copy the example file and fill in your values:

```bash
cd FullstackApp/Backend
cp .env.example .env
```

Then edit `.env`:

```env
# Django core
SECRET_KEY=your-long-random-secret-key-here
DEBUG=True

# PostgreSQL database
DB_NAME=pagesage_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# AI Services
GEMINI_API_KEY=your-gemini-api-key
GEMINI_API_KEY_MANIM=your-gemini-api-key-for-manim
DEEPGRAM_API_KEY=your-deepgram-api-key
GROQ_API_KEY=your-groq-api-key
```

**Notes:**
- `SECRET_KEY` — generate one with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG` — set to `False` in production
- Two separate Gemini keys are used so the RAG/quiz quota doesn't interfere with Manim animation generation — you can use the same key for both if quota allows
- The `.env` file is gitignored and must never be committed

---

### Third-Party Services

You need accounts and API keys for the following services:

#### 1. Google Gemini AI
- **Used for:** RAG Q&A (`GEMINI_API_KEY`), Manim code generation (`GEMINI_API_KEY_MANIM`), quiz generation (`GEMINI_API_KEY`)
- **Model used:** `gemini-2.5-flash` (all three pipelines)
- **Get key:** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Free tier available

#### 2. Groq
- **Used for:** Lecture narration generation (LLaMA 3.1 8B)
- **Model used:** `llama-3.1-8b-instant`
- **Get key:** [https://console.groq.com/keys](https://console.groq.com/keys)
- Free tier available (rate limited ~10 req/min — pipeline auto-retries on 429)

#### 3. Deepgram
- **Used for:** Text-to-Speech conversion of narrations → MP3
- **Voice used:** `aura-2-orpheus-en`
- **Get key:** [https://console.deepgram.com](https://console.deepgram.com)
- Free tier: 200 characters/request limit; pipeline auto-truncates and retries

---

### Database Setup

```bash
# Make sure PostgreSQL is running and the database exists:
psql -U postgres -c "CREATE DATABASE pagesage_db;"

# Activate venv and run migrations:
cd FullstackApp/Backend
venv\Scripts\activate   # Windows
python manage.py migrate

# (Optional) Seed the database with demo data:
python manage.py seed
# Creates:
#   Teacher: teacher@pagesageai.com / test1234
#   Student: student@demo.com / test1234
#   4 demo classes (enrollment code for one: DEMO01)

# (Optional) Seed data for load testing:
python manage.py seed_load_test
# Creates READY AI courses, quizzes and animations so Locust can exercise all endpoints
```

---

### Running the Application

**Terminal 1 — Backend:**
```bash
cd FullstackApp/Backend
venv\Scripts\activate
python manage.py runserver
# API available at http://localhost:8000
# Note: Django StatReloader may print a RuntimeWarning on startup — this is harmless
# Add --noreload to suppress it: python manage.py runserver --noreload
```

**Terminal 2 — Frontend:**
```bash
cd FullstackApp/Frontend/frontend-app
npm run dev
# UI available at http://localhost:5173
```

**CORS:** The backend only allows requests from `http://localhost:5173`. If you change the frontend port, update `CORS_ALLOWED_ORIGINS` in `core/settings/local.py`.

---

### Configurable Constants

These values live in `FullstackApp/Backend/api/constants.py` and can be changed without touching any other file:

| Constant | Default | Description |
|----------|---------|-------------|
| `QUIZ_QUESTION_COUNT` | `20` | Number of MCQ questions generated per quiz |
| `QUIZ_OPTION_COUNT` | `4` | Number of answer options per question (A–D) |
| `MIN_GRADE` | `0` | Minimum grade for assignment submissions |
| `MAX_GRADE` | `100` | Maximum grade for assignment submissions |
| `CLASS_CODE_LENGTH` | `6` | Length of the auto-generated class enrollment code |
| `MANIM_RENDER_TIMEOUT_SECONDS` | `180` | Seconds before a Manim render is killed (3 min) |

---

### AI Model Settings

These live in `FullstackApp/Backend/core/settings/base.py` and apply across all environments:

| Setting | Default | Description |
|---------|---------|-------------|
| `RAG_LLM_MODEL` | `gemini-2.5-flash` | Gemini model for RAG Q&A and reformulation |
| `RAG_LLM_TEMPERATURE` | `0.3` | Lower = more factual RAG answers |
| `RAG_TOP_K` | `4` | Number of ChromaDB chunks retrieved per query |
| `QUIZ_LLM_MODEL` | `gemini-2.5-flash` | Gemini model for quiz generation |
| `QUIZ_LLM_TEMPERATURE` | `0.3` | Lower = more structured quiz output |
| `MANIM_LLM_MODEL` | `gemini-2.5-flash` | Gemini model for Manim code generation |
| `MANIM_LLM_TEMPERATURE` | `0.2` | Very low = more deterministic code output |
| `EMBEDDINGS_MODEL` | `all-MiniLM-L6-v2` | HuggingFace sentence embeddings for ChromaDB |
| `RAG_CHUNK_SIZE` | `700` | Characters per ChromaDB text chunk |
| `RAG_CHUNK_OVERLAP` | `100` | Overlap between consecutive chunks |
| `OSSU_CHROMA_DIR` | `Backend/chroma_ossu_db` | Path to the persistent ChromaDB directory |

**JWT Token Lifetimes** (in `core/settings/base.py`):
- Access token: **5 minutes** — short-lived for security
- Refresh token: **1 day**

**Narration model** (in `api/services/narration.py`):
- `DEFAULT_MODEL = "llama-3.1-8b-instant"` — Groq model for lecture narration
- `WORDS_PER_MINUTE = 130` — used to calculate target narration length per slide
- `MIN_SECONDS_PER_SLIDE = 20` / `MAX_SECONDS_PER_SLIDE = 110` — bounds for auto narration duration

**TTS settings** (in `api/services/tts.py`):
- `DEFAULT_VOICE = "aura-2-orpheus-en"` — Deepgram voice; alternatives: `aura-2-zeus-en`, `aura-2-hermes-en`, `aura-2-jupiter-en`
- `RATE_LIMIT_DELAY = 6.5` — seconds between TTS requests (Deepgram free tier limit)
- `MAX_RETRIES = 5` — retry attempts on network/rate-limit errors

**Manim animation** (in `api/services/manim_pipeline.py`):
- `MAX_RETRIES = 3` — retries if Manim rendering fails
- Scene class must always be named `ConceptScene`
- Renders at `-ql` (low quality) for speed; change to `-qh` for high quality (much slower)

---

### Running Tests

**Unit + Performance Tests (78 tests, ~2 min):**
```bash
cd FullstackApp/Backend
venv\Scripts\activate
python manage.py test api.tests.unit -v 2
# Or use the runner script:
.\api\tests\unit\run_unit_tests.ps1
```

**Load Tests (Locust, requires running server + seed_load_test):**
```bash
cd FullstackApp/Backend
venv\Scripts\activate
.\api\tests\load\run_load_test.ps1
# Runs 20 virtual users (6 teachers + 14 students) for 60 seconds
# Generates HTML report in api/tests/load/reports/
```
