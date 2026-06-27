"""
Seed date pentru load testing — creează AI courses READY, quiz și animații
astfel încât toate endpoint-urile din Module 3-6 să fie exercitate de Locust.

Rulare: python manage.py seed_load_test
"""
import struct
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from api.models import Class, AICourse, Quiz, ConceptAnimation
from api.constants import QUIZ_QUESTION_COUNT, QUIZ_OPTION_COUNT

User = get_user_model()

MEDIA_ROOT = Path(settings.MEDIA_ROOT)


def _make_png(path: Path):
    """Scrie un PNG valid minimal (1×1 pixel roșu) pe disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # PNG header + IHDR + IDAT + IEND
    png = (
        b'\x89PNG\r\n\x1a\n'                          # signature
        b'\x00\x00\x00\rIHDR'                          # IHDR length + type
        + struct.pack('>II', 1, 1)                     # width=1, height=1
        + b'\x08\x02\x00\x00\x00'                      # 8-bit RGB, no interlace
        + b'\x90wS\xde'                                # IHDR CRC
        + b'\x00\x00\x00\x0cIDAT'                      # IDAT length + type
        + b'x\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05'   # zlib compressed 1px
        + b'\x18\xd8N'                                  # IDAT CRC
        + b'\x00\x00\x00\x00IEND\xaeB`\x82'            # IEND
    )
    path.write_bytes(png)


def _sample_questions():
    return [
        {
            'question': f'Întrebarea {i + 1}: Ce returnează funcția f(x) = x²?',
            'options':  [f'x^{j}' for j in range(QUIZ_OPTION_COUNT)],
            'correct_index': 0,
        }
        for i in range(QUIZ_QUESTION_COUNT)
    ]


class Command(BaseCommand):
    help = 'Seed date READY pentru load testing (AI courses, quiz, animații)'

    def handle(self, *args, **options):
        # ── găsim clasa CS (student e înrolat) ───────────────────────────────
        cs = Class.objects.filter(code='CS101').first()
        if not cs:
            self.stderr.write('Rulează mai întâi: python manage.py seed')
            return

        # ── găsim clasa DEMO01 (teacher are acces) ───────────────────────────
        demo = Class.objects.filter(code='DEMO01').first()

        # ── AI Course READY pentru CS (acces student) ────────────────────────
        cs_course = AICourse.objects.filter(class_obj=cs, title='Load Test Course').first()
        if not cs_course:
            out_dir = MEDIA_ROOT / 'ai_courses' / 'load_test_cs'
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'audio').mkdir(exist_ok=True)

            # pagini dummy
            for i in range(1, 4):
                _make_png(out_dir / f'page_{i:04d}.png')

            cs_course = AICourse.objects.create(
                class_obj=cs,
                title='Load Test Course',
                filename='load_test.pdf',
                status='READY',
                output_dir=str(out_dir),
                total_pages=3,
            )
            self.stdout.write(f'  AI Course READY creat pentru CS (id={cs_course.id})')
        else:
            self.stdout.write(f'  AI Course CS deja există (id={cs_course.id})')

        # ── Quiz READY pentru CS course ───────────────────────────────────────
        if not hasattr(cs_course, 'quiz') or not Quiz.objects.filter(ai_course=cs_course).exists():
            Quiz.objects.create(
                ai_course=cs_course,
                status='READY',
                questions=_sample_questions(),
            )
            self.stdout.write('  Quiz READY creat pentru CS course')
        else:
            self.stdout.write('  Quiz CS deja există')

        # ── Animații READY pentru CS course ──────────────────────────────────
        concepts = [
            ('Binary Search Tree', 'binary search tree'),
            ('Quicksort Algorithm', 'quicksort algorithm'),
            ('Dijkstra Shortest Path', 'dijkstra shortest path'),
        ]
        for concept, key in concepts:
            ConceptAnimation.objects.get_or_create(
                ai_course=cs_course,
                concept_key=key,
                defaults={'concept': concept, 'status': 'READY'},
            )
        self.stdout.write(f'  {len(concepts)} animații READY create pentru CS course')

        # ── AI Course READY pentru DEMO01 (acces teacher) ────────────────────
        if demo:
            demo_course = AICourse.objects.filter(class_obj=demo, title='Load Test Course').first()
            if not demo_course:
                out_dir = MEDIA_ROOT / 'ai_courses' / 'load_test_demo'
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / 'audio').mkdir(exist_ok=True)
                for i in range(1, 4):
                    _make_png(out_dir / f'page_{i:04d}.png')

                demo_course = AICourse.objects.create(
                    class_obj=demo,
                    title='Load Test Course',
                    filename='load_test.pdf',
                    status='READY',
                    output_dir=str(out_dir),
                    total_pages=3,
                )
                self.stdout.write(f'  AI Course READY creat pentru DEMO01 (id={demo_course.id})')

            if not Quiz.objects.filter(ai_course=demo_course).exists():
                Quiz.objects.create(
                    ai_course=demo_course,
                    status='READY',
                    questions=_sample_questions(),
                )
                self.stdout.write('  Quiz READY creat pentru DEMO01 course')

        self.stdout.write(self.style.SUCCESS('\nSeed load test complet! Pornește acum: python -m locust ...'))
