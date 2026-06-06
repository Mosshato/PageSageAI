"""
Generează două diagrame:
  1. PostgreSQL ER Diagram — toate modelele Django
  2. ChromaDB RAG Diagram — structura colecțiilor și fluxul de date

Rulează cu: python generate_diagrams.py
Dependențe: pip install matplotlib
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

COLORS = {
    'auth':   '#4f46e5',
    'acad':   '#0891b2',
    'assign': '#059669',
    'lecture':'#d97706',
    'ai':     '#dc2626',
    'header': '#1e293b',
    'bg':     '#f8fafc',
    'line':   '#64748b',
    'pk':     '#fbbf24',
    'fk':     '#a78bfa',
}


def draw_table(ax, x, y, width, title, fields, color):
    row_h = 0.32
    header_h = 0.42
    total_h = header_h + len(fields) * row_h + 0.12

    shadow = FancyBboxPatch((x + 0.04, y - total_h - 0.04), width, total_h,
                             boxstyle="round,pad=0.05", linewidth=0,
                             facecolor='#00000022', zorder=1)
    ax.add_patch(shadow)

    body = FancyBboxPatch((x, y - total_h), width, total_h,
                           boxstyle="round,pad=0.05", linewidth=1.2,
                           edgecolor=color, facecolor='white', zorder=2)
    ax.add_patch(body)

    header = FancyBboxPatch((x, y - header_h), width, header_h,
                             boxstyle="round,pad=0.05", linewidth=0,
                             facecolor=color, zorder=3)
    ax.add_patch(header)

    ax.text(x + width / 2, y - header_h / 2, title,
            ha='center', va='center', fontsize=8.5, fontweight='bold',
            color='white', zorder=4)

    for i, (fname, ftype, fkind) in enumerate(fields):
        fy = y - header_h - (i + 0.5) * row_h - 0.06
        if i % 2 == 0:
            ax.add_patch(FancyBboxPatch((x + 0.04, fy - row_h / 2 + 0.04),
                                        width - 0.08, row_h - 0.04,
                                        boxstyle="square,pad=0", linewidth=0,
                                        facecolor='#f1f5f9', zorder=2))
        badge_color = COLORS['pk'] if fkind == 'PK' else COLORS['fk'] if fkind == 'FK' else None
        if badge_color:
            ax.add_patch(FancyBboxPatch((x + 0.07, fy - 0.1), 0.28, 0.20,
                                        boxstyle="round,pad=0.02", linewidth=0,
                                        facecolor=badge_color, zorder=4))
            ax.text(x + 0.21, fy, fkind, ha='center', va='center',
                    fontsize=5.5, fontweight='bold', color='white', zorder=5)
            name_x = x + 0.42
        else:
            name_x = x + 0.12

        ax.text(name_x, fy, fname, ha='left', va='center',
                fontsize=6.8, color=COLORS['header'], zorder=4)
        ax.text(x + width - 0.08, fy, ftype, ha='right', va='center',
                fontsize=6.2, color='#94a3b8', style='italic', zorder=4)

    return total_h


def arrow(ax, x1, y1, x2, y2, label='', color='#64748b'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2,
                                connectionstyle='arc3,rad=0.08'), zorder=5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, label, ha='center', va='center', fontsize=5.5,
                color=color, bbox=dict(facecolor='white', edgecolor='none', pad=1))


def draw_postgres_diagram():
    fig, ax = plt.subplots(figsize=(22, 16))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 16)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    ax.text(11, 15.6, 'PostgreSQL — ER Diagram', ha='center', va='top',
            fontsize=16, fontweight='bold', color=COLORS['header'])
    ax.text(11, 15.25, 'PageSage AI · Bachelor Thesis Database Schema', ha='center',
            va='top', fontsize=9, color='#64748b')

    W = 3.6

    # User
    user_fields = [
        ('id',         'serial',    'PK'),
        ('email',      'varchar',   ''),
        ('first_name', 'varchar',   ''),
        ('last_name',  'varchar',   ''),
        ('role',       'varchar',   ''),
        ('is_active',  'boolean',   ''),
        ('is_staff',   'boolean',   ''),
        ('password',   'varchar',   ''),
        ('created_at', 'timestamp', ''),
    ]
    ux, uy = 9.0, 15.0
    uh = draw_table(ax, ux, uy, W, 'User', user_fields, COLORS['auth'])

    # Class
    cls_fields = [
        ('id',           'serial',    'PK'),
        ('teacher_id',   'int',       'FK'),
        ('name',         'varchar',   ''),
        ('teacher_name', 'varchar',   ''),
        ('code',         'varchar',   ''),
        ('color',        'varchar',   ''),
        ('icon',         'varchar',   ''),
        ('created_at',   'timestamp', ''),
    ]
    cx, cy = 0.5, 15.0
    ch = draw_table(ax, cx, cy, W, 'Class', cls_fields, COLORS['acad'])

    # Enrollment
    enr_fields = [
        ('id',            'serial',    'PK'),
        ('class_obj_id',  'int',       'FK'),
        ('student_email', 'varchar',   ''),
        ('student_name',  'varchar',   ''),
        ('joined_at',     'timestamp', ''),
    ]
    ex, ey = 0.5, 10.2
    draw_table(ax, ex, ey, W, 'Enrollment', enr_fields, COLORS['acad'])

    # Announcement
    ann_fields = [
        ('id',           'serial',    'PK'),
        ('class_obj_id', 'int',       'FK'),
        ('title',        'varchar',   ''),
        ('body',         'text',      ''),
        ('pinned',       'boolean',   ''),
        ('created_at',   'timestamp', ''),
    ]
    ax2, ay = 4.5, 15.0
    draw_table(ax, ax2, ay, W, 'Announcement', ann_fields, COLORS['acad'])

    # Assignment
    asgn_fields = [
        ('id',           'serial',    'PK'),
        ('class_obj_id', 'int',       'FK'),
        ('title',        'varchar',   ''),
        ('description',  'text',      ''),
        ('due_date',     'date',      ''),
        ('points',       'int',       ''),
        ('grade',        'int',       ''),
        ('status',       'varchar',   ''),
        ('created_at',   'timestamp', ''),
    ]
    asx, asy = 4.5, 9.5
    draw_table(ax, asx, asy, W, 'Assignment', asgn_fields, COLORS['assign'])

    # AssignmentAttachment
    att_fields = [
        ('id',            'serial',  'PK'),
        ('assignment_id', 'int',     'FK'),
        ('name',          'varchar', ''),
        ('file',          'varchar', ''),
    ]
    atx, aty = 4.5, 5.4
    draw_table(ax, atx, aty, W, 'AssignmentAttachment', att_fields, COLORS['assign'])

    # Submission
    sub_fields = [
        ('id',            'serial',    'PK'),
        ('assignment_id', 'int',       'FK'),
        ('student_email', 'varchar',   ''),
        ('submitted_at',  'timestamp', ''),
        ('grade',         'int',       ''),
        ('note',          'text',      ''),
    ]
    sbx, sby = 8.4, 9.5
    draw_table(ax, sbx, sby, W, 'Submission', sub_fields, COLORS['assign'])

    # SubmissionFile
    sf_fields = [
        ('id',            'serial',  'PK'),
        ('submission_id', 'int',     'FK'),
        ('name',          'varchar', ''),
        ('file',          'varchar', ''),
    ]
    sfx, sfy = 8.4, 5.6
    draw_table(ax, sfx, sfy, W, 'SubmissionFile', sf_fields, COLORS['assign'])

    # Lecture
    lec_fields = [
        ('id',           'serial',    'PK'),
        ('class_obj_id', 'int',       'FK'),
        ('title',        'varchar',   ''),
        ('description',  'text',      ''),
        ('duration',     'varchar',   ''),
        ('date',         'date',      ''),
        ('created_at',   'timestamp', ''),
    ]
    lx, ly = 0.5, 6.8
    draw_table(ax, lx, ly, W, 'Lecture', lec_fields, COLORS['lecture'])

    # LectureFile
    lf_fields = [
        ('id',         'serial',  'PK'),
        ('lecture_id', 'int',     'FK'),
        ('name',       'varchar', ''),
        ('file',       'varchar', ''),
    ]
    lfx, lfy = 0.5, 3.1
    draw_table(ax, lfx, lfy, W, 'LectureFile', lf_fields, COLORS['lecture'])

    # AICourse
    aic_fields = [
        ('id',           'serial',    'PK'),
        ('class_obj_id', 'int',       'FK'),
        ('title',        'varchar',   ''),
        ('filename',     'varchar',   ''),
        ('status',       'varchar',   ''),
        ('current_step', 'varchar',   ''),
        ('total_pages',  'int',       ''),
        ('error_msg',    'text',      ''),
        ('output_dir',   'varchar',   ''),
        ('created_at',   'timestamp', ''),
    ]
    aicx, aicy = 13.0, 15.0
    aich = draw_table(ax, aicx, aicy, W, 'AICourse', aic_fields, COLORS['ai'])

    # ConceptAnimation
    canim_fields = [
        ('id',           'serial',    'PK'),
        ('ai_course_id', 'int',       'FK'),
        ('concept',      'text',      ''),
        ('concept_key',  'varchar',   ''),
        ('status',       'varchar',   ''),
        ('video_file',   'varchar',   ''),
        ('retry_count',  'int',       ''),
        ('error_msg',    'text',      ''),
        ('created_at',   'timestamp', ''),
    ]
    canx, cany = 13.0, 9.8
    draw_table(ax, canx, cany, W, 'ConceptAnimation', canim_fields, COLORS['ai'])

    # Quiz
    quiz_fields = [
        ('id',           'serial',    'PK'),
        ('ai_course_id', 'int',       'FK'),
        ('status',       'varchar',   ''),
        ('questions',    'jsonb',     ''),
        ('error_msg',    'text',      ''),
        ('created_at',   'timestamp', ''),
    ]
    qx, qy = 17.2, 15.0
    draw_table(ax, qx, qy, W, 'Quiz', quiz_fields, COLORS['ai'])

    # QuizAttempt
    qa_fields = [
        ('id',            'serial',    'PK'),
        ('quiz_id',       'int',       'FK'),
        ('student_id',    'int',       'FK'),
        ('answers',       'jsonb',     ''),
        ('score',         'int',       ''),
        ('correct_count', 'int',       ''),
        ('completed_at',  'timestamp', ''),
    ]
    qax, qay = 17.2, 9.6
    draw_table(ax, qax, qay, W, 'QuizAttempt', qa_fields, COLORS['ai'])

    # Relatii
    c = COLORS['line']
    arrow(ax, cx + W, cy - 0.2,   ux, uy - 0.2,           'teacher', c)
    arrow(ax, ex + W/2, ey,       cx + W/2, cy - ch,       '', c)
    arrow(ax, ax2 + W/2, ay,      cx + W/2, cy - ch + 0.1, '', c)
    arrow(ax, asx + 0.5, asy,     cx + W/2, cy - ch + 0.15,'', c)
    arrow(ax, atx + W/2, aty,     asx + W/2, asy - 2.9,    '', c)
    arrow(ax, sbx, sby - 1.0,     asx + W, asy - 1.0,      '', c)
    arrow(ax, sfx + W/2, sfy,     sbx + W/2, sby - 2.1,    '', c)
    arrow(ax, lx + W/2, ly,       cx + W/2, cy - ch + 0.2, '', c)
    arrow(ax, lfx + W/2, lfy,     lx + W/2, ly - 2.5,      '', c)
    arrow(ax, aicx, aicy - 0.2,   cx + W, cy - 0.4,        '', c)
    arrow(ax, canx + W/2, cany,   aicx + W/2, aicy - aich, '', c)
    arrow(ax, qx, qy - 0.3,       aicx + W, aicy - 0.3,    '1:1', '#dc2626')
    arrow(ax, qax + W/2, qay,     qx + W/2, qy - 2.5,      '', c)
    arrow(ax, qax, qay - 0.6,     ux + W, uy - 0.6,        'student', c)

    legend_items = [
        mpatches.Patch(color=COLORS['auth'],   label='Auth'),
        mpatches.Patch(color=COLORS['acad'],   label='Academic'),
        mpatches.Patch(color=COLORS['assign'], label='Assignment / Submission'),
        mpatches.Patch(color=COLORS['lecture'],label='Lecture'),
        mpatches.Patch(color=COLORS['ai'],     label='AI Features'),
        mpatches.Patch(color=COLORS['pk'],     label='PK — Primary Key'),
        mpatches.Patch(color=COLORS['fk'],     label='FK — Foreign Key'),
    ]
    ax.legend(handles=legend_items, loc='lower right', fontsize=7,
              framealpha=0.95, edgecolor='#cbd5e1', title='Legend', title_fontsize=7.5)

    plt.tight_layout(pad=0.5)
    plt.savefig('postgres_er_diagram.png', dpi=180, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print('[OK] Salvat: postgres_er_diagram.png')


def draw_chroma_diagram():
    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis('off')
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')

    def box(x, y, w, h, color, radius=0.3):
        p = FancyBboxPatch((x, y), w, h,
                           boxstyle=f"round,pad={radius}", linewidth=1.5,
                           edgecolor=color, facecolor=color + '33',
                           zorder=3)
        ax.add_patch(p)

    def lbl(x, y, text, size=8, color='white', bold=False, ha='center'):
        ax.text(x, y, text, ha=ha, va='center', fontsize=size,
                fontweight='bold' if bold else 'normal', color=color, zorder=5)

    def farrow(x1, y1, x2, y2, color='#94a3b8', txt=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.8), zorder=4)
        if txt:
            ax.text((x1+x2)/2, (y1+y2)/2 + 0.18, txt,
                    ha='center', fontsize=6.5, color=color, zorder=5)

    lbl(9, 10.6, 'ChromaDB — RAG Architecture', size=14, bold=True)
    lbl(9, 10.2, 'PageSage AI · Retrieval-Augmented Generation Pipeline', size=8.5, color='#94a3b8')

    # Surse
    lbl(2.5, 9.6, 'Data Sources', size=9, bold=True, color='#7dd3fc')
    box(0.4, 8.2, 4.2, 1.1, '#0891b2')
    lbl(2.5, 8.75, '📄 OSSU Curriculum', size=8.5, bold=True, color='#7dd3fc')
    lbl(2.5, 8.35, 'GitHub README.md  ·  Core CS section', size=7, color='#bae6fd')

    box(0.4, 6.7, 4.2, 1.2, '#7c3aed')
    lbl(2.5, 7.35, '📚 AICourse PDF Pages', size=8.5, bold=True, color='#c4b5fd')
    lbl(2.5, 6.95, 'page_XXXX_narration.json', size=7, color='#ddd6fe')
    lbl(2.5, 6.73, 'Prefix: [Course {id} | Page {n}]', size=6.5, color='#a78bfa')

    # Procesare
    lbl(7.5, 9.6, 'Processing', size=9, bold=True, color='#86efac')
    box(5.4, 8.1, 4.2, 1.2, '#059669')
    lbl(7.5, 8.75, 'Text Splitter', size=8.5, bold=True, color='#86efac')
    lbl(7.5, 8.38, 'RecursiveCharacterTextSplitter', size=7, color='#bbf7d0')
    lbl(7.5, 8.17, 'chunk_size=700  ·  overlap=100', size=6.5, color='#6ee7b7')

    box(5.4, 6.5, 4.2, 1.3, '#d97706')
    lbl(7.5, 7.2, 'Embeddings Model', size=8.5, bold=True, color='#fde68a')
    lbl(7.5, 6.85, 'HuggingFace  all-MiniLM-L6-v2', size=7, color='#fef3c7')
    lbl(7.5, 6.63, '384-dim vectors  ·  runs locally', size=6.5, color='#fcd34d')

    # ChromaDB
    lbl(12.5, 9.6, 'ChromaDB (Persistent)', size=9, bold=True, color='#f9a8d4')
    box(10.4, 5.5, 4.2, 4.0, '#be185d')
    lbl(12.5, 9.1, 'chroma_ossu_db/', size=8.5, bold=True, color='#fbcfe8')

    box(10.7, 7.9, 3.6, 1.3, '#9d174d', radius=0.2)
    lbl(12.5, 8.6, 'Collection: langchain', size=7.5, bold=True, color='#fce7f3')
    lbl(12.5, 8.3, 'Shared  ·  single persistent dir', size=6.5, color='#fbcfe8')
    lbl(12.5, 8.05, '(OSSU + all AICourse chunks)', size=6.5, color='#f9a8d4')

    box(10.7, 6.3, 3.6, 1.3, '#9d174d', radius=0.2)
    lbl(12.5, 7.02, 'Document Entry', size=7.5, bold=True, color='#fce7f3')
    lbl(12.5, 6.72, 'id  ·  embedding (384-d)', size=6.5, color='#fbcfe8')
    lbl(12.5, 6.52, 'document (chunk text)', size=6.5, color='#fbcfe8')
    lbl(12.5, 6.32, 'metadata  {source, page, ...}', size=6.5, color='#fbcfe8')

    box(10.7, 5.6, 3.6, 0.5, '#9d174d', radius=0.15)
    lbl(12.5, 5.855, 'chroma_indexed.marker  (per-course)', size=6.5, color='#fce7f3')

    # Query pipeline
    lbl(9, 4.8, 'Query Pipeline  (RAG)', size=9, bold=True, color='#fca5a5')

    box(0.4, 3.3, 3.2, 1.1, '#dc2626')
    lbl(2.0, 3.9, 'Student Question', size=8, bold=True, color='#fca5a5')
    lbl(2.0, 3.5, 'POST /ai-courses/{id}/ask/', size=6.5, color='#fecaca')

    box(4.1, 3.3, 3.2, 1.1, '#dc2626')
    lbl(5.7, 3.9, 'Query Embedding', size=8, bold=True, color='#fca5a5')
    lbl(5.7, 3.5, 'same MiniLM model', size=6.5, color='#fecaca')

    box(7.8, 3.3, 3.2, 1.1, '#dc2626')
    lbl(9.4, 3.9, 'Similarity Search', size=8, bold=True, color='#fca5a5')
    lbl(9.4, 3.5, 'top-k chunks (ChromaDB)', size=6.5, color='#fecaca')

    box(11.5, 3.3, 3.2, 1.1, '#dc2626')
    lbl(13.1, 3.9, 'Gemini 2.5 Flash', size=8, bold=True, color='#fca5a5')
    lbl(13.1, 3.5, 'Answer generation (LLM)', size=6.5, color='#fecaca')

    box(14.9, 3.3, 2.8, 1.1, '#dc2626')
    lbl(16.3, 3.9, 'Response', size=8, bold=True, color='#fca5a5')
    lbl(16.3, 3.5, 'JSON answer', size=6.5, color='#fecaca')

    # Sageti ingestie
    ac = '#38bdf8'
    farrow(4.6, 8.75, 5.4, 8.75, ac, 'chunks')
    farrow(4.6, 7.3,  5.4, 7.3,  ac)
    farrow(7.5, 8.1,  7.5, 7.8,  ac, 'docs')
    farrow(9.6, 8.75, 10.4, 8.35, ac, 'split')
    farrow(9.6, 7.3,  10.4, 7.5,  ac, 'embed + store')

    # Sageti query
    qc = '#f87171'
    farrow(3.6,  3.85, 4.1,  3.85, qc)
    farrow(7.3,  3.85, 7.8,  3.85, qc)
    farrow(11.0, 3.85, 11.5, 3.85, qc)
    farrow(14.7, 3.85, 14.9, 3.85, qc)
    farrow(12.5, 5.5,  9.4,  4.4,  '#f9a8d4', 'top-k docs')

    ax.text(0.5, 0.35,
            '* OSSU chunks sunt seed-uite o singura data prin createDB.py.\n'
            '  AICourse chunks sunt adaugate per-curs in pasul CHROMA al pipeline-ului.\n'
            '  Ambele impart aceeasi colectie ChromaDB.',
            fontsize=6.5, color='#64748b', va='bottom')

    plt.tight_layout(pad=0.3)
    plt.savefig('chromadb_rag_diagram.png', dpi=180, bbox_inches='tight', facecolor='#0f172a')
    plt.close()
    print('[OK] Salvat: chromadb_rag_diagram.png')


if __name__ == '__main__':
    print('Generez diagrame...')
    draw_postgres_diagram()
    draw_chroma_diagram()
    print('\nGata! Fisiere generate:')
    print('  -> postgres_er_diagram.png')
    print('  -> chromadb_rag_diagram.png')
