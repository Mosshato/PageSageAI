"""
PageSage AI — Load Testing Entry Point
=======================================
TeacherUser (weight=3) — ~6 din 20 utilizatori  — Module 1, 2, 3, 6
StudentUser (weight=7) — ~14 din 20 utilizatori  — Module 1, 2, 3, 4, 5, 6

RULARE
------
  python manage.py seed
  python manage.py seed_load_test
  python -m locust -f api/tests/load/locustfile.py --host http://localhost:8000

  Web UI: http://localhost:8089 → 20 users, spawn rate 2 → Start swarming
"""
import random
from locust import HttpUser, task, between, events

from api.tests.load.base import (
    PageSageUser,
    TEACHER_EMAIL, TEACHER_PASSWORD,
    STUDENT_EMAIL, STUDENT_PASSWORD,
)
from api.tests.load.tasks import (
    module1_auth,
    module2_classroom,
    module3_pdf,
    module4_rag,
    module5_animation,
    module6_quiz,
)


# ─────────────────────────────────────────────────────────────────────────────
#  TEACHER USER  — Module 1, 2, 3, 6
# ─────────────────────────────────────────────────────────────────────────────

class TeacherUser(PageSageUser):
    weight    = 3
    wait_time = between(1, 3)

    def on_start(self):
        if not self._login(TEACHER_EMAIL, TEACHER_PASSWORD, "teacher"):
            return
        r = self.client.get("/api/teacher/classes/", headers=self._h(),
                            name="[M2] GET /api/teacher/classes/ [setup]")
        if r.status_code == 200 and r.json():
            self.class_id  = r.json()[0]["id"]
            self.class_ids = [c["id"] for c in r.json()]
            self._discover_ai_data(self.class_ids)

    # Module 1
    @task(4)
    def get_me(self):
        module1_auth.get_me(self)

    @task(1)
    def refresh_token(self):
        module1_auth.refresh_token(self)

    # Module 2
    @task(6)
    def list_teacher_classes(self):
        module2_classroom.list_teacher_classes(self)

    @task(4)
    def teacher_class_detail(self):
        module2_classroom.teacher_class_detail(self)

    @task(2)
    def teacher_stats(self):
        module2_classroom.teacher_stats(self)

    @task(2)
    def teacher_students(self):
        module2_classroom.teacher_students(self)

    # Module 3
    @task(5)
    def list_ai_courses(self):
        module3_pdf.list_ai_courses(self)

    @task(3)
    def ai_course_status(self):
        module3_pdf.ai_course_status(self)

    @task(2)
    def ai_course_page(self):
        module3_pdf.ai_course_page(self)

    # Module 6
    @task(2)
    def quiz_results(self):
        module6_quiz.quiz_results(self)


# ─────────────────────────────────────────────────────────────────────────────
#  STUDENT USER  — Module 1, 2, 3, 4, 5, 6
# ─────────────────────────────────────────────────────────────────────────────

class StudentUser(PageSageUser):
    weight    = 7
    wait_time = between(1, 4)

    def on_start(self):
        if not self._login(STUDENT_EMAIL, STUDENT_PASSWORD, "student"):
            return
        r = self.client.get("/api/classes/", headers=self._h(),
                            name="[M2] GET /api/classes/ [setup]")
        if r.status_code == 200:
            self.class_ids = [c["id"] for c in r.json()]
            self._discover_ai_data(self.class_ids)

    # Module 1
    @task(4)
    def get_me(self):
        module1_auth.get_me(self)

    @task(1)
    def refresh_token(self):
        module1_auth.refresh_token(self)

    # Module 2
    @task(7)
    def list_classes(self):
        module2_classroom.list_classes(self)

    @task(5)
    def class_detail(self):
        module2_classroom.class_detail(self)

    @task(6)
    def list_assignments(self):
        module2_classroom.list_assignments(self)

    @task(3)
    def account_stats(self):
        module2_classroom.account_stats(self)

    # Module 3
    @task(5)
    def list_ai_courses(self):
        module3_pdf.list_ai_courses(self)

    @task(3)
    def ai_course_status(self):
        module3_pdf.ai_course_status(self)

    @task(2)
    def ai_course_page(self):
        module3_pdf.ai_course_page(self)

    # Module 4
    @task(4)
    def ask_question(self):
        module4_rag.ask_question(self)

    @task(2)
    def reformulate_answer(self):
        module4_rag.reformulate_answer(self)

    # Module 5
    @task(4)
    def list_animations(self):
        module5_animation.list_animations(self)

    @task(3)
    def animation_status(self):
        module5_animation.animation_status(self)

    @task(2)
    def request_animation(self):
        module5_animation.request_animation(self)

    # Module 6
    @task(4)
    def quiz_status(self):
        module6_quiz.quiz_status(self)

    @task(3)
    def quiz_questions(self):
        module6_quiz.quiz_questions(self)

    @task(2)
    def submit_quiz_attempt(self):
        module6_quiz.submit_quiz_attempt(self)


# ─────────────────────────────────────────────────────────────────────────────
#  RAPORT AUTOMAT LA FINAL
# ─────────────────────────────────────────────────────────────────────────────

@events.quitting.add_listener
def _on_quitting(environment, **kwargs):
    import os
    from datetime import datetime

    stats     = environment.runner.stats
    now       = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    tag       = now.strftime("%Y%m%d_%H%M%S")
    total     = stats.total.num_requests
    failures  = stats.total.num_failures
    fail_pct  = (failures / total * 100) if total > 0 else 0.0
    avg_ms    = stats.total.avg_response_time
    med_ms    = stats.total.get_response_time_percentile(0.50)
    p95_ms    = stats.total.get_response_time_percentile(0.95)
    p99_ms    = stats.total.get_response_time_percentile(0.99)

    sep = "=" * 70
    print(f"\n{sep}\n  PAGESAGE AI — LOAD TEST RESULTS  |  {timestamp}")
    print(f"  Requests: {total}  |  Failures: {failures} ({fail_pct:.1f}%)")
    print(f"  Avg: {avg_ms:.0f}ms  |  p50: {med_ms:.0f}ms  |  p95: {p95_ms:.0f}ms  |  p99: {p99_ms:.0f}ms")
    print(sep)

    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, f"load_report_{tag}.md")

    module_map = {"M1": "Auth", "M2": "Classroom", "M3": "PDF Pipeline",
                  "M4": "RAG", "M5": "Animation", "M6": "Quiz"}

    rows = []
    for entry in sorted(stats.entries.values(), key=lambda e: e.num_requests, reverse=True):
        module = next((v for k, v in module_map.items() if f"[{k}]" in entry.name), "—")
        name   = entry.name.split("] ", 1)[-1]
        rows.append(
            f"| `{name}` | {module} | {entry.num_requests} | {entry.num_failures} "
            f"| {entry.avg_response_time:.0f} | {entry.get_response_time_percentile(0.50):.0f} "
            f"| {entry.get_response_time_percentile(0.95):.0f} |"
        )

    md = "\n".join([
        "# PageSage AI — Load Test Report",
        f"\n**Data:** {timestamp}  \n**Utilizatori:** 20 (6 profesori + 14 studenți)  \n**Durată:** 60s\n",
        "## Sumar General\n",
        "| Metrică | Valoare |", "|---------|---------|",
        f"| Total cereri | **{total}** |",
        f"| Cereri eșuate | {failures} ({fail_pct:.1f}%) |",
        f"| Avg | **{avg_ms:.0f} ms** |",
        f"| p50 | {med_ms:.0f} ms |",
        f"| p95 | {p95_ms:.0f} ms |",
        f"| p99 | {p99_ms:.0f} ms |\n",
        "## Statistici per Endpoint\n",
        "| Endpoint | Modul | Cereri | Eșecuri | Avg (ms) | p50 (ms) | p95 (ms) |",
        "|----------|-------|--------|---------|----------|----------|----------|",
        *rows,
        "\n*Raport generat automat — PageSage AI Load Testing Suite.*",
    ])

    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  [REPORT] {path}\n{sep}\n")
