import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_facecolor('#F8F9FA')
fig.patch.set_facecolor('#F8F9FA')

# ── helpers ──────────────────────────────────────────────────────────────────

def box(ax, x, y, w, h, label, sublabel=None,
        fc='#4A90D9', ec='#2C5F8A', text_color='white',
        fontsize=10, radius=0.3, bold=True):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0.05,rounding_size={radius}",
                          facecolor=fc, edgecolor=ec, linewidth=2, zorder=3)
    ax.add_patch(rect)
    cy = y + h / 2 + (0.15 if sublabel else 0)
    ax.text(x + w / 2, cy, label,
            ha='center', va='center', fontsize=fontsize,
            color=text_color, fontweight='bold' if bold else 'normal',
            zorder=4)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 - 0.28, sublabel,
                ha='center', va='center', fontsize=7.5,
                color=text_color, alpha=0.85, zorder=4)

def section_bg(ax, x, y, w, h, label, fc='#E8F4FD', ec='#B0C4DE'):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.1,rounding_size=0.4",
                          facecolor=fc, edgecolor=ec, linewidth=1.5,
                          linestyle='--', zorder=1)
    ax.add_patch(rect)
    ax.text(x + 0.2, y + h - 0.28, label,
            ha='left', va='top', fontsize=8, color=ec,
            fontweight='bold', zorder=2)

def arrow(ax, x1, y1, x2, y2, label='', color='#555555', style='->', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle='arc3,rad=0.0'),
                zorder=5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha='center', va='bottom',
                fontsize=7, color=color, style='italic', zorder=6)

def double_arrow(ax, x1, y1, x2, y2, label='', color='#555555', lw=1.5):
    arrow(ax, x1, y1, x2, y2, label, color, '<->', lw)

# ── TITLE ────────────────────────────────────────────────────────────────────
ax.text(10, 13.5, 'PageSage AI — System Architecture',
        ha='center', va='center', fontsize=16, fontweight='bold', color='#1A1A2E')

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1 — FRONTEND  (y 10.5 – 13.0)
# ═══════════════════════════════════════════════════════════════════════════
section_bg(ax, 0.4, 10.3, 8.8, 2.6, 'Frontend  (React / Vite  •  localhost:5173)',
           fc='#EAF6FF', ec='#5B9BD5')

# Student UI
box(ax, 0.7, 11.2, 3.8, 1.4,
    '🎓  Student UI',
    'Dashboard · Classes · AI Teach\nAnimations · Quizzes · Calendar',
    fc='#2E86AB', ec='#1A5276', fontsize=9)

# Teacher UI
box(ax, 5.0, 11.2, 3.8, 1.4,
    '👩‍🏫  Teacher UI',
    'Dashboard · Classes · PDF Upload\nStudents · Quiz Results',
    fc='#1B6CA8', ec='#0D3F6B', fontsize=9)

# Auth context note
box(ax, 1.8, 10.45, 5.6, 0.6,
    'AuthContext  •  JWT in localStorage  •  ProtectedRoute',
    fc='#5B9BD5', ec='#2C5F8A', fontsize=8, radius=0.2)

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2 — BACKEND  (y 6.0 – 10.0)
# ═══════════════════════════════════════════════════════════════════════════
section_bg(ax, 0.4, 5.8, 8.8, 4.3,
           'Backend  (Django REST Framework  •  localhost:8000)',
           fc='#FFF8E7', ec='#D4A017')

# Auth views
box(ax, 0.7, 8.7, 2.5, 1.0,
    'auth_views.py',
    'JWT signup/login\ntoken refresh',
    fc='#E67E22', ec='#A04000', fontsize=8.5)

# Main views
box(ax, 3.4, 8.7, 2.5, 1.0,
    'views.py',
    'Classes · Assignments\nSubmissions · Lectures',
    fc='#E67E22', ec='#A04000', fontsize=8.5)

# Serializers
box(ax, 6.1, 8.7, 2.8, 1.0,
    'serializers.py',
    'Student / Teacher\nvariants',
    fc='#CA6F1E', ec='#784212', fontsize=8.5)

# AI Pipeline
box(ax, 0.7, 7.3, 2.5, 1.1,
    'ai_pipeline.py',
    'PDF→PNG→Narration\n→TTS→ChromaDB',
    fc='#8E44AD', ec='#5B2C6F', fontsize=8)

# Manim Pipeline
box(ax, 3.4, 7.3, 2.5, 1.1,
    'manim_pipeline.py',
    'Gemini→Manim code\n→mp4 render',
    fc='#8E44AD', ec='#5B2C6F', fontsize=8)

# Quiz Pipeline
box(ax, 6.1, 7.3, 2.8, 1.1,
    'quiz_pipeline.py',
    'Narration→Gemini\n→20 MCQs',
    fc='#8E44AD', ec='#5B2C6F', fontsize=8)

# Media files
box(ax, 1.5, 6.05, 6.2, 0.9,
    '📁  media/  (submissions · attachments · ai_courses · animations)',
    fc='#95A5A6', ec='#616A6B', fontsize=8, radius=0.2)

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3 — DATABASES  (y 2.8 – 5.5)
# ═══════════════════════════════════════════════════════════════════════════
section_bg(ax, 0.4, 2.6, 8.8, 2.8,
           'Data Layer',
           fc='#F0FFF0', ec='#27AE60')

# PostgreSQL
box(ax, 0.7, 3.0, 3.8, 2.1,
    '🐘  PostgreSQL',
    'Users · Classes · Enrollments\nAssignments · Submissions\nAICourse · Quiz · Attempts\nConceptAnimation',
    fc='#27AE60', ec='#1A7A40', fontsize=8.5)

# ChromaDB
box(ax, 5.0, 3.0, 3.8, 2.1,
    '🔍  ChromaDB  (RAG)',
    'chroma_ossu_db/\nOSSU curriculum chunks\n+ Course page chunks\n[Course {id} | Page {n}]',
    fc='#16A085', ec='#0E6655', fontsize=8.5)

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 4 — EXTERNAL APIs  (y 0.3 – 2.4)
# ═══════════════════════════════════════════════════════════════════════════
section_bg(ax, 0.4, 0.3, 19.0, 2.2,
           'External APIs  &  Third-Party Services',
           fc='#FFF0F5', ec='#C0392B')

box(ax, 0.7, 0.6, 3.2, 1.5,
    '🤖  Google Gemini',
    'gemini-2.5-flash\nNarration · RAG · Quiz\nManim code gen',
    fc='#C0392B', ec='#7B241C', fontsize=8.5)

box(ax, 4.2, 0.6, 3.2, 1.5,
    '🎙  Deepgram TTS',
    'Narration text\n→ MP3 audio\nper page',
    fc='#C0392B', ec='#7B241C', fontsize=8.5)

box(ax, 7.7, 0.6, 3.2, 1.5,
    '🎬  Manim CLI',
    'manim -ql\nConceptScene → .mp4\n(local subprocess)',
    fc='#922B21', ec='#641E16', fontsize=8.5)

box(ax, 11.2, 0.6, 3.2, 1.5,
    '🔐  JWT  (SimpleJWT)',
    'Access token: 5 min\nRefresh token: 1 day\nRole in payload',
    fc='#784212', ec='#4A235A', fontsize=8.5)

box(ax, 14.7, 0.6, 4.0, 1.5,
    '📦  Django + DRF',
    'REST framework\nORM · Migrations\nMedia file serving',
    fc='#1A5276', ec='#0D2B45', fontsize=8.5)

# ═══════════════════════════════════════════════════════════════════════════
# RIGHT SIDE — HTTP / WS flow label
# ═══════════════════════════════════════════════════════════════════════════
section_bg(ax, 9.6, 5.8, 9.8, 7.7,
           'Communication Flow',
           fc='#F5F5FF', ec='#7F8C8D')

# HTTP REST box
box(ax, 9.9, 11.2, 4.2, 1.4,
    '🌐  HTTP REST',
    'Bearer JWT\nContent-Type: JSON\nCORS: localhost:5173',
    fc='#2980B9', ec='#1A5276', fontsize=8.5)

# Polling box
box(ax, 14.5, 11.2, 4.5, 1.4,
    '🔄  Polling',
    'Animation status: 4 s\nAI pipeline: /status\nQuiz: /quiz/status',
    fc='#2980B9', ec='#1A5276', fontsize=8.5)

# Daemon Threads box
box(ax, 9.9, 9.3, 9.1, 1.5,
    '🧵  Background Daemon Threads',
    'AICourse pipeline  •  Manim render  •  Quiz generation\n'
    'Idempotent steps — safe to resume on restart',
    fc='#6C3483', ec='#4A235A', fontsize=8.5)

# File System box
box(ax, 9.9, 7.5, 9.1, 1.4,
    '💾  File System  (Backend/media/)',
    'PNG pages  •  MP3 audio  •  Narration JSON\n'
    'Animation MP4  •  PDF uploads  •  Submissions',
    fc='#616A6B', ec='#2C3E50', fontsize=8.5)

# RAG flow box
box(ax, 9.9, 5.95, 9.1, 1.2,
    '🔗  RAG Query Flow',
    'Student question → embedding → ChromaDB top-k → Gemini → answer',
    fc='#148F77', ec='#0E6655', fontsize=8.5)

# ═══════════════════════════════════════════════════════════════════════════
# ARROWS
# ═══════════════════════════════════════════════════════════════════════════

# Frontend ↔ Backend
double_arrow(ax, 4.6, 10.3, 4.6, 9.7, 'HTTP /api/', '#2C3E50', 2)

# Backend ↔ PostgreSQL
double_arrow(ax, 3.0, 5.8, 3.0, 5.1, 'Django ORM', '#27AE60', 2)

# Backend ↔ ChromaDB
double_arrow(ax, 6.5, 5.8, 6.5, 5.1, 'chromadb client', '#16A085', 2)

# ai_pipeline → Gemini
arrow(ax, 1.95, 7.3, 1.95, 2.1, '', '#C0392B', '->', 1.5)

# ai_pipeline → Deepgram
arrow(ax, 2.3, 7.3, 5.0, 2.1, '', '#C0392B', '->', 1.5)

# manim_pipeline → Gemini
arrow(ax, 4.0, 7.3, 2.5, 2.1, '', '#C0392B', '->', 1.5)

# manim_pipeline → Manim CLI
arrow(ax, 4.65, 7.3, 8.9, 2.1, '', '#922B21', '->', 1.5)

# quiz_pipeline → Gemini
arrow(ax, 7.5, 7.3, 3.0, 2.1, '', '#C0392B', '->', 1.5)

# Comm flow ↔ Backend (HTTP REST)
double_arrow(ax, 9.9, 11.9, 9.3, 9.2, 'JWT Bearer', '#2980B9', 1.5)

# Daemon threads ↔ Backend pipelines
double_arrow(ax, 9.9, 9.8, 9.3, 8.1, '', '#6C3483', 1.5)

# File system ↔ media
double_arrow(ax, 9.9, 8.0, 8.9, 6.5, '', '#616A6B', 1.5)

# RAG flow ↔ ChromaDB + Gemini
arrow(ax, 9.9, 6.5, 8.9, 4.8, '', '#148F77', '->', 1.5)

# ═══════════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════════
legend_items = [
    (mpatches.Patch(fc='#2E86AB', ec='#1A5276'), 'Frontend Components'),
    (mpatches.Patch(fc='#E67E22', ec='#A04000'), 'Backend Views'),
    (mpatches.Patch(fc='#8E44AD', ec='#5B2C6F'), 'AI Pipelines'),
    (mpatches.Patch(fc='#27AE60', ec='#1A7A40'), 'Databases'),
    (mpatches.Patch(fc='#C0392B', ec='#7B241C'), 'External APIs'),
    (mpatches.Patch(fc='#6C3483', ec='#4A235A'), 'Background Threads'),
]
handles, labels = zip(*legend_items)
ax.legend(handles, labels, loc='lower right', fontsize=8,
          framealpha=0.9, edgecolor='#CCCCCC', ncol=2)

plt.tight_layout()
plt.savefig('system_architecture.png', dpi=180, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print("Saved: system_architecture.png")
plt.show()
