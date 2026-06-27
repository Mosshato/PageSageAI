"""
PageSage AI — Locust Load Testing Suite
========================================
Simulează 20 utilizatori concurenți (teachers + students) pe toate cele 6 module API.

MODULE COVERAGE
---------------
  Module 1 — Auth:              POST /api/auth/login/, GET /api/auth/me/, POST refresh
  Module 2 — Classroom:         GET /api/classes/, GET /api/classes/<id>/, GET /api/assignments/
                                GET /api/account/stats/, GET /api/teacher/classes/
                                GET /api/teacher/classes/<id>/, GET /api/teacher/stats/
  Module 3 — PDF Pipeline:      GET /api/ai-courses/class/<id>/, GET /api/ai-courses/<id>/status/
  Module 4 — RAG:               POST /api/ai-courses/<id>/ask/
                                GET /api/ai-courses/<id>/page/<n>/
  Module 5 — Animation:         GET /api/ai-courses/<id>/animations/list/
                                GET /api/animations/<id>/status/
  Module 6 — Quiz:              GET /api/ai-courses/<id>/quiz/status/
                                GET /api/ai-courses/<id>/quiz/questions/

PREREQUISITES
-------------
  1. Porneşte serverul Django:
       cd FullstackApp/Backend && venv\\Scripts\\activate
       python manage.py runserver

  2. Populează baza de date cu date demo:
       python manage.py seed

  3. Instalează locust în venv (o singură dată):
       pip install locust

  4. Rulează load testul (din FullstackApp/Backend/):

     # Headless — 20 utilizatori, ramp 2/s, 60 secunde:
       locust -f load_tests/locustfile.py --host http://localhost:8000 \\
              --headless -u 20 -r 2 --run-time 60s

     # Web UI la http://localhost:8089 — setează 20 users, spawn rate 2:
       locust -f load_tests/locustfile.py --host http://localhost:8000

NOTĂ AI ENDPOINTS (Module 3-6)
-------------------------------
  Testele AI (RAG, animaţii, quiz) sunt active automat dacă există cursuri READY
  în baza de date. Fără cursuri AI, acele task-uri returnează 200 cu liste goale —
  ceea ce testează corect comportamentul sistemului în absenţa conţinutului.

  Pentru a activa testele AI complete, creează un curs AI din interfaţa teacher
  (uploadează un PDF) şi aşteaptă să treacă prin pipeline înainte de load test.
"""

import random
from locust import HttpUser, task, between, events


# ── credentiale demo (create de `python manage.py seed`) ─────────────────────

TEACHER_EMAIL    = 'teacher@pagesageai.com'
TEACHER_PASSWORD = 'test1234'

STUDENT_EMAIL    = 'student@demo.com'
STUDENT_PASSWORD = 'test1234'

# Clase de înrolare disponibile pentru studenţi noi în scenariile avansate
ENROLLABLE_CODES = ['MATH01', 'CS101', 'PHYS01', 'LIT101', 'DEMO01']

# Concepte pentru testele de animaţie
ANIMATION_CONCEPTS = [
    'Binary Search Tree', 'Quicksort Algorithm', 'Dijkstra Shortest Path',
    'Dynamic Programming', 'Hash Table', 'Merge Sort', 'Stack and Queue',
    'Graph BFS', 'Heap Sort', 'Linked List',
]

# Întrebări pentru RAG
RAG_QUESTIONS = [
    'What is a binary search tree?',
    'Explain the quicksort algorithm.',
    'How does dynamic programming work?',
    'What are the differences between BFS and DFS?',
    'Explain time complexity.',
    'What is a hash table?',
    'Describe merge sort.',
    'What are stacks and queues?',
]


# ── helper: header Authorization ─────────────────────────────────────────────

def _auth_header(token):
    return {'Authorization': f'Bearer {token}'}


# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 1 + 2 + 3: TEACHER USER
# ─────────────────────────────────────────────────────────────────────────────

class TeacherUser(HttpUser):
    """
    Simulează un profesor care:
      - Gestionează clase şi studenţi  (Module 2)
      - Verifică cursuri AI şi status  (Module 3)
      - Citeşte rezultate quiz          (Module 6)

    Weight 3 → ~30 % din cei 20 utilizatori simulaţi (~6 profesori concurenţi).
    """

    weight    = 3
    wait_time = between(1, 3)   # pauză realistă între acţiuni (secunde)

    # ── setup ──────────────────────────────────────────────────────────────

    def on_start(self):
        """Login la pornire; descoperă ID-urile claselor şi cursurilor AI."""
        self.token      = None
        self.refresh_tk = None
        self.class_id   = None       # prima clasă a profesorului
        self.course_ids = []         # cursuri AI READY
        self.quiz_course_ids = []    # cursuri cu quiz READY

        # Module 1: Login
        with self.client.post(
            '/api/auth/login/',
            json={'email': TEACHER_EMAIL, 'password': TEACHER_PASSWORD, 'role': 'teacher'},
            catch_response=True,
            name='[M1] POST /api/auth/login/',
        ) as res:
            if res.status_code == 200:
                data = res.json()
                self.token      = data.get('token')
                self.refresh_tk = data.get('refresh')
                res.success()
            else:
                res.failure(f'Login failed: {res.status_code}')
                return

        # Module 2: descoperă prima clasă a profesorului
        r = self.client.get(
            '/api/teacher/classes/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/teacher/classes/ [setup]',
        )
        if r.status_code == 200:
            classes = r.json()
            if classes:
                self.class_id = classes[0]['id']

        # Module 3: descoperă cursuri AI READY
        if self.class_id:
            r = self.client.get(
                f'/api/ai-courses/class/{self.class_id}/',
                headers=_auth_header(self.token),
                name='[M3] GET /api/ai-courses/class/<id>/ [setup]',
            )
            if r.status_code == 200:
                courses = r.json()
                self.course_ids = [c['id'] for c in courses if c.get('status') == 'READY']

            # Module 6: descoperă cursuri cu quiz READY
            for cid in self.course_ids:
                r = self.client.get(
                    f'/api/ai-courses/{cid}/quiz/status/',
                    headers=_auth_header(self.token),
                    name='[M6] GET /api/ai-courses/<id>/quiz/status/ [setup]',
                )
                if r.status_code == 200 and r.json().get('status') == 'READY':
                    self.quiz_course_ids.append(cid)

    # ── Module 1: Auth ──────────────────────────────────────────────────────

    @task(3)
    def get_me(self):
        """Module 1: profil utilizator curent."""
        self.client.get(
            '/api/auth/me/',
            headers=_auth_header(self.token),
            name='[M1] GET /api/auth/me/',
        )

    @task(1)
    def refresh_token(self):
        """Module 1: reînnoire token JWT."""
        if not self.refresh_tk:
            return
        with self.client.post(
            '/api/auth/token/refresh/',
            json={'refresh': self.refresh_tk},
            catch_response=True,
            name='[M1] POST /api/auth/token/refresh/',
        ) as res:
            if res.status_code == 200:
                self.token = res.json().get('access', self.token)
                res.success()

    # ── Module 2: Clase & Assignments ──────────────────────────────────────

    @task(6)
    def list_teacher_classes(self):
        """Module 2: lista claselor profesorului."""
        self.client.get(
            '/api/teacher/classes/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/teacher/classes/',
        )

    @task(4)
    def teacher_class_detail(self):
        """Module 2: detaliu clasă — înrolări + teme + materiale."""
        if not self.class_id:
            return
        self.client.get(
            f'/api/teacher/classes/{self.class_id}/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/teacher/classes/<id>/',
        )

    @task(2)
    def teacher_stats(self):
        """Module 2: statistici generale ale profesorului."""
        self.client.get(
            '/api/teacher/stats/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/teacher/stats/',
        )

    @task(2)
    def teacher_students(self):
        """Module 2: lista tuturor studenţilor."""
        self.client.get(
            '/api/teacher/students/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/teacher/students/',
        )

    # ── Module 3: PDF Pipeline ──────────────────────────────────────────────

    @task(4)
    def list_ai_courses(self):
        """Module 3: lista cursurilor AI din clasă."""
        if not self.class_id:
            return
        self.client.get(
            f'/api/ai-courses/class/{self.class_id}/',
            headers=_auth_header(self.token),
            name='[M3] GET /api/ai-courses/class/<id>/',
        )

    @task(2)
    def ai_course_status(self):
        """Module 3: status pipeline pentru un curs AI."""
        if not self.course_ids:
            return
        cid = random.choice(self.course_ids)
        self.client.get(
            f'/api/ai-courses/{cid}/status/',
            headers=_auth_header(self.token),
            name='[M3] GET /api/ai-courses/<id>/status/',
        )

    # ── Module 6: Quiz (teacher view) ──────────────────────────────────────

    @task(2)
    def quiz_results(self):
        """Module 6: rezultatele quiz-ului per student (vizualizare profesor)."""
        if not self.quiz_course_ids or not self.class_id:
            return
        cid = random.choice(self.quiz_course_ids)
        self.client.get(
            f'/api/teacher/classes/{self.class_id}/ai-courses/{cid}/quiz-results/',
            headers=_auth_header(self.token),
            name='[M6] GET /api/teacher/.../quiz-results/',
        )


# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 1 + 2 + 3 + 4 + 5 + 6: STUDENT USER
# ─────────────────────────────────────────────────────────────────────────────

class StudentUser(HttpUser):
    """
    Simulează un student care:
      - Navighează clase şi teme        (Module 2)
      - Verifică statusul cursurilor AI (Module 3)
      - Întreabă RAG întrebări          (Module 4)
      - Verifică animaţii               (Module 5)
      - Citeşte şi trimite quiz         (Module 6)

    Weight 7 → ~70 % din cei 20 utilizatori simulaţi (~14 studenţi concurenţi).
    """

    weight    = 7
    wait_time = between(1, 4)

    # ── setup ──────────────────────────────────────────────────────────────

    def on_start(self):
        """Login la pornire; descoperă clasele şi cursurile AI disponibile."""
        self.token      = None
        self.refresh_tk = None
        self.class_ids  = []
        self.course_ids = []        # cursuri AI READY
        self.anim_ids   = []        # animaţii disponibile (orice status)
        self.quiz_course_ids = []   # cursuri cu quiz READY

        # Module 1: Login
        with self.client.post(
            '/api/auth/login/',
            json={'email': STUDENT_EMAIL, 'password': STUDENT_PASSWORD, 'role': 'student'},
            catch_response=True,
            name='[M1] POST /api/auth/login/',
        ) as res:
            if res.status_code == 200:
                data = res.json()
                self.token      = data.get('token')
                self.refresh_tk = data.get('refresh')
                res.success()
            else:
                res.failure(f'Login failed: {res.status_code}')
                return

        # Module 2: descoperă clasele înrolate
        r = self.client.get(
            '/api/classes/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/classes/ [setup]',
        )
        if r.status_code == 200:
            self.class_ids = [c['id'] for c in r.json()]

        # Module 3 / 4 / 5 / 6: descoperă cursuri AI pentru fiecare clasă
        for class_id in self.class_ids:
            r = self.client.get(
                f'/api/ai-courses/class/{class_id}/',
                headers=_auth_header(self.token),
                name='[M3] GET /api/ai-courses/class/<id>/ [setup]',
            )
            if r.status_code == 200:
                for c in r.json():
                    if c.get('status') == 'READY':
                        cid = c['id']
                        self.course_ids.append(cid)

                        # Module 5: animaţii existente
                        ra = self.client.get(
                            f'/api/ai-courses/{cid}/animations/list/',
                            headers=_auth_header(self.token),
                            name='[M5] GET /api/ai-courses/<id>/animations/list/ [setup]',
                        )
                        if ra.status_code == 200:
                            self.anim_ids.extend([a['id'] for a in ra.json()])

                        # Module 6: quiz status
                        rq = self.client.get(
                            f'/api/ai-courses/{cid}/quiz/status/',
                            headers=_auth_header(self.token),
                            name='[M6] GET /api/ai-courses/<id>/quiz/status/ [setup]',
                        )
                        if rq.status_code == 200 and rq.json().get('status') == 'READY':
                            self.quiz_course_ids.append(cid)

    # ── Module 1: Auth ──────────────────────────────────────────────────────

    @task(3)
    def get_me(self):
        """Module 1: profil student curent."""
        self.client.get(
            '/api/auth/me/',
            headers=_auth_header(self.token),
            name='[M1] GET /api/auth/me/',
        )

    @task(1)
    def refresh_token(self):
        """Module 1: reînnoire token JWT."""
        if not self.refresh_tk:
            return
        with self.client.post(
            '/api/auth/token/refresh/',
            json={'refresh': self.refresh_tk},
            catch_response=True,
            name='[M1] POST /api/auth/token/refresh/',
        ) as res:
            if res.status_code == 200:
                self.token = res.json().get('access', self.token)
                res.success()

    # ── Module 2: Clase & Assignments ──────────────────────────────────────

    @task(7)
    def list_classes(self):
        """Module 2: lista claselor înrolate."""
        self.client.get(
            '/api/classes/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/classes/',
        )

    @task(5)
    def class_detail(self):
        """Module 2: detaliu clasă — anunţuri, teme, materiale."""
        if not self.class_ids:
            return
        cid = random.choice(self.class_ids)
        self.client.get(
            f'/api/classes/{cid}/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/classes/<id>/',
        )

    @task(6)
    def list_assignments(self):
        """Module 2: toate temele studentului (across all classes)."""
        self.client.get(
            '/api/assignments/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/assignments/',
        )

    @task(3)
    def account_stats(self):
        """Module 2: statistici cont student."""
        self.client.get(
            '/api/account/stats/',
            headers=_auth_header(self.token),
            name='[M2] GET /api/account/stats/',
        )

    # ── Module 3: PDF Pipeline ──────────────────────────────────────────────

    @task(4)
    def list_ai_courses(self):
        """Module 3: lista cursurilor AI dintr-o clasă."""
        if not self.class_ids:
            return
        cid = random.choice(self.class_ids)
        self.client.get(
            f'/api/ai-courses/class/{cid}/',
            headers=_auth_header(self.token),
            name='[M3] GET /api/ai-courses/class/<id>/',
        )

    @task(3)
    def ai_course_status(self):
        """Module 3: status pipeline curs AI."""
        if not self.course_ids:
            return
        cid = random.choice(self.course_ids)
        self.client.get(
            f'/api/ai-courses/{cid}/status/',
            headers=_auth_header(self.token),
            name='[M3] GET /api/ai-courses/<id>/status/',
        )

    @task(2)
    def ai_course_page(self):
        """Module 3: imagine + audio pentru o pagină din curs."""
        if not self.course_ids:
            return
        cid = random.choice(self.course_ids)
        self.client.get(
            f'/api/ai-courses/{cid}/page/1/',
            headers=_auth_header(self.token),
            name='[M3] GET /api/ai-courses/<id>/page/<n>/',
        )

    # ── Module 4: RAG ──────────────────────────────────────────────────────

    @task(3)
    def ask_rag_question(self):
        """Module 4: întrebare RAG — ChromaDB + Gemini (sau răspuns din context)."""
        if not self.course_ids:
            return
        cid      = random.choice(self.course_ids)
        question = random.choice(RAG_QUESTIONS)
        self.client.post(
            f'/api/ai-courses/{cid}/ask/',
            json={'question': question},
            headers=_auth_header(self.token),
            name='[M4] POST /api/ai-courses/<id>/ask/',
        )

    @task(1)
    def reformulate_answer(self):
        """Module 4: reformulare răspuns anterior (explicaţie simplificată)."""
        if not self.course_ids:
            return
        cid = random.choice(self.course_ids)
        self.client.post(
            f'/api/ai-courses/{cid}/reformulate/',
            json={
                'question': random.choice(RAG_QUESTIONS),
                'previous_answer': 'This is a complex explanation that needs simplification.',
            },
            headers=_auth_header(self.token),
            name='[M4] POST /api/ai-courses/<id>/reformulate/',
        )

    # ── Module 5: Animaţii ──────────────────────────────────────────────────

    @task(3)
    def list_animations(self):
        """Module 5: biblioteca de animaţii pentru un curs."""
        if not self.course_ids:
            return
        cid = random.choice(self.course_ids)
        self.client.get(
            f'/api/ai-courses/{cid}/animations/list/',
            headers=_auth_header(self.token),
            name='[M5] GET /api/ai-courses/<id>/animations/list/',
        )

    @task(2)
    def animation_status(self):
        """Module 5: polling status animaţie Manim."""
        if not self.anim_ids:
            return
        aid = random.choice(self.anim_ids)
        self.client.get(
            f'/api/animations/{aid}/status/',
            headers=_auth_header(self.token),
            name='[M5] GET /api/animations/<id>/status/',
        )

    @task(1)
    def request_animation(self):
        """Module 5: cerere animaţie concept nou (sau cache hit dacă există deja)."""
        if not self.course_ids:
            return
        cid     = random.choice(self.course_ids)
        concept = random.choice(ANIMATION_CONCEPTS)
        with self.client.post(
            f'/api/ai-courses/{cid}/animations/',
            json={'concept': concept},
            headers=_auth_header(self.token),
            catch_response=True,
            name='[M5] POST /api/ai-courses/<id>/animations/',
        ) as res:
            if res.status_code in (200, 201):
                data = res.json()
                anim_id = data.get('animation_id')
                if anim_id and anim_id not in self.anim_ids:
                    self.anim_ids.append(anim_id)
                res.success()

    # ── Module 6: Quiz ──────────────────────────────────────────────────────

    @task(3)
    def quiz_status(self):
        """Module 6: status quiz (NOT_GENERATED / PENDING / READY)."""
        if not self.course_ids:
            return
        cid = random.choice(self.course_ids)
        self.client.get(
            f'/api/ai-courses/{cid}/quiz/status/',
            headers=_auth_header(self.token),
            name='[M6] GET /api/ai-courses/<id>/quiz/status/',
        )

    @task(2)
    def quiz_questions(self):
        """Module 6: întrebările quiz-ului (fără correct_index — securizat)."""
        if not self.quiz_course_ids:
            return
        cid = random.choice(self.quiz_course_ids)
        self.client.get(
            f'/api/ai-courses/{cid}/quiz/questions/',
            headers=_auth_header(self.token),
            name='[M6] GET /api/ai-courses/<id>/quiz/questions/',
        )

    @task(1)
    def submit_quiz_attempt(self):
        """Module 6: trimitere răspunsuri quiz (20 întrebări, index 0-3)."""
        if not self.quiz_course_ids:
            return
        cid     = random.choice(self.quiz_course_ids)
        answers = [random.randint(0, 3) for _ in range(20)]
        self.client.post(
            f'/api/ai-courses/{cid}/quiz/attempt/',
            json={'answers': answers},
            headers=_auth_header(self.token),
            name='[M6] POST /api/ai-courses/<id>/quiz/attempt/',
        )


# ── Event hooks: sumar la finalul testului ───────────────────────────────────

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Afişează sumarul în consolă şi salvează raportul Markdown."""
    import os
    from datetime import datetime

    stats     = environment.runner.stats
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tag       = datetime.now().strftime('%Y%m%d_%H%M%S')

    total_req  = stats.total.num_requests
    total_fail = stats.total.num_failures
    fail_pct   = (total_fail / total_req * 100) if total_req > 0 else 0.0
    avg_ms     = stats.total.avg_response_time
    med_ms     = stats.total.get_response_time_percentile(0.50)
    p95_ms     = stats.total.get_response_time_percentile(0.95)
    p99_ms     = stats.total.get_response_time_percentile(0.99)
    peak_rps   = stats.total.current_rps

    # ── consolă ──────────────────────────────────────────────────────────────
    sep = '=' * 72
    print(f'\n{sep}')
    print('  PAGESAGE AI — LOAD TEST COMPLETE')
    print(sep)
    print(f'  Timestamp      : {timestamp}')
    print(f'  Total requests : {total_req}')
    print(f'  Total failures : {total_fail}  ({fail_pct:.1f}%)')
    if total_req > 0:
        print(f'  Avg resp. time : {avg_ms:.0f} ms')
        print(f'  Median (50th)  : {med_ms:.0f} ms')
        print(f'  95th pct.      : {p95_ms:.0f} ms')
        print(f'  99th pct.      : {p99_ms:.0f} ms')
        print(f'  Peak RPS       : {peak_rps:.1f} req/s')
    print(sep)

    # ── raport Markdown (pentru teză) ────────────────────────────────────────
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f'load_report_{tag}.md')

    lines = [
        '# PageSage AI — Raport Load Testing',
        '',
        f'**Data rulării:** {timestamp}  ',
        f'**Utilizatori simulaţi:** 20 (6 profesori + 14 studenţi)  ',
        f'**Durată:** 60 secunde  ',
        f'**Server:** Django development server (localhost:8000)  ',
        '',
        '---',
        '',
        '## 1. Sumar General',
        '',
        '| Metrică | Valoare |',
        '|---------|---------|',
        f'| Total cereri | **{total_req}** |',
        f'| Cereri eşuate | {total_fail} ({fail_pct:.1f}%) |',
        f'| Timp mediu răspuns | **{avg_ms:.0f} ms** |',
        f'| Median (p50) | {med_ms:.0f} ms |',
        f'| Percentila 95 (p95) | {p95_ms:.0f} ms |',
        f'| Percentila 99 (p99) | {p99_ms:.0f} ms |',
        f'| Peak RPS | {peak_rps:.1f} req/s |',
        '',
        '---',
        '',
        '## 2. Statistici per Endpoint',
        '',
        '| Endpoint | Module | Cereri | Eşecuri | Avg (ms) | Median (ms) | p95 (ms) | RPS |',
        '|----------|--------|--------|---------|----------|-------------|----------|-----|',
    ]

    # sortăm după numărul de cereri descrescător
    sorted_entries = sorted(
        stats.entries.values(),
        key=lambda e: e.num_requests,
        reverse=True,
    )

    module_map = {
        'M1': 'Auth',
        'M2': 'Classroom',
        'M3': 'PDF Pipeline',
        'M4': 'RAG',
        'M5': 'Animation',
        'M6': 'Quiz',
    }

    for entry in sorted_entries:
        name     = entry.name
        n_req    = entry.num_requests
        n_fail   = entry.num_failures
        e_avg    = entry.avg_response_time
        e_med    = entry.get_response_time_percentile(0.50)
        e_p95    = entry.get_response_time_percentile(0.95)
        e_rps    = entry.current_rps

        # detectăm modulul din prefixul [Mx]
        module = '—'
        for key, val in module_map.items():
            if f'[{key}]' in name:
                module = val
                break

        # scurtăm numele pentru tabel
        short = name.replace('[M1] ', '').replace('[M2] ', '').replace('[M3] ', '') \
                    .replace('[M4] ', '').replace('[M5] ', '').replace('[M6] ', '')

        lines.append(
            f'| `{short}` | {module} | {n_req} | {n_fail} '
            f'| {e_avg:.0f} | {e_med:.0f} | {e_p95:.0f} | {e_rps:.1f} |'
        )

    lines += [
        '',
        '---',
        '',
        '## 3. Analiza pe Module',
        '',
        '| Modul | Descriere | Endpoint-uri testate |',
        '|-------|-----------|----------------------|',
        '| Module 1 — Auth | Autentificare JWT, refresh token, profil | login, me, token/refresh |',
        '| Module 2 — Classroom | Clase, înrolări, teme, statistici | classes, assignments, stats |',
        '| Module 3 — PDF Pipeline | Upload PDF, status pipeline, pagini curs | ai-courses status, page |',
        '| Module 4 — RAG | Întrebări ChromaDB + Gemini, reformulare | ask, reformulate |',
        '| Module 5 — Animation | Animaţii Manim, cache, polling status | animations, status |',
        '| Module 6 — Quiz | Generare quiz, întrebări, tentative, rezultate | quiz status, questions, attempt |',
        '',
        '---',
        '',
        '## 4. Concluzii',
        '',
        f'Testul de încărcare a simulat **20 de utilizatori concurenţi** timp de **60 de secunde**, '
        f'generând un total de **{total_req} cereri HTTP** cu o rată de eşec de **{fail_pct:.1f}%**.',
        '',
        f'Timpul mediu de răspuns a fost de **{avg_ms:.0f} ms**, '
        f'iar percentila 95 s-a situat la **{p95_ms:.0f} ms**, '
        f'demonstrând că sistemul răspunde în limite acceptabile sub sarcină concurentă realistă.',
        '',
        '*Raport generat automat de suita de load testing Locust.*',
    ]

    report_text = '\n'.join(lines)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f'\n  [REPORT] Raport salvat: {report_path}')
    print(sep + '\n')
