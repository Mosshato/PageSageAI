# PageSage AI

An AI-powered educational platform for teachers and students, built as a Bachelor's thesis project.

## Features

- **Class Management** — Teachers create classes with enrollment codes; students join and access course materials
- **AI Lectures** — Upload a PDF and the platform auto-generates narration, text-to-speech audio, and indexes content for Q&A
- **RAG-Powered Q&A** — Students ask questions about lecture content; answers are generated using semantic search + Gemini
- **Concept Animations** — Students request a concept and get an AI-generated Manim animation rendered as MP4
- **AI Quizzes** — Teachers trigger quiz generation from lecture content; students take MCQ tests and scores are tracked
- **Assignments & Submissions** — Teachers post assignments, students submit work, teachers grade and give feedback
- **Role-Based Access** — Separate dashboards for teachers and students with JWT authentication

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Frontend | React 19, Vite, React Router |
| Database | PostgreSQL (prod), SQLite (dev) |
| AI | Google Gemini 2.5 Flash, Deepgram, ChromaDB |
| Animation | Manim (ManimGL) |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally
- API keys: Gemini, Deepgram

### Backend

```bash
cd Project/FullstackApp/Backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy the env template and fill in your credentials:

```bash
cp .env.example .env
# then edit .env with your SECRET_KEY, DB credentials, GEMINI_API_KEY, DEEPGRAM_API_KEY
cp core/settings.example.py core/settings.py
```

Then:

```bash
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd Project/FullstackApp/Frontend/frontend-app
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Demo Credentials

Run the seed script to populate demo data:

```bash
python manage.py seed_demo   # creates sample teacher, student, and classes
```

## Project Structure

```
Project/
├── FullstackApp/
│   ├── Backend/       # Django REST API
│   └── Frontend/      # React/Vite SPA
├── Functionalities/
│   ├── PDFExtraction/ # PDF → text/image pipeline
│   └── RAG/           # ChromaDB vector store setup
└── CodeGenerationModel/
```

## License

Academic project — Bachelor's Thesis, 2026.
