"""
Base class for all PageSage AI load test users.

Provides:
  - login / token refresh helpers
  - shared state: token, refresh_tk, class_ids, course_ids, anim_ids, quiz_course_ids
  - _h()  → Authorization header dict
  - abstract = True  → Locust will not instantiate this class directly
"""
from locust import HttpUser, between

TEACHER_EMAIL    = "teacher@pagesageai.com"
TEACHER_PASSWORD = "test1234"
STUDENT_EMAIL    = "student@demo.com"
STUDENT_PASSWORD = "test1234"


class PageSageUser(HttpUser):
    abstract   = True
    wait_time  = between(1, 3)

    # shared state — set during on_start
    token           = None
    refresh_tk      = None
    class_ids       = []   # enrolled / owned class IDs
    class_id        = None # primary class (teacher)
    course_ids      = []   # READY AI course IDs
    quiz_course_ids = []   # course IDs that have a READY quiz
    anim_ids        = []   # existing animation IDs

    # ── helpers ──────────────────────────────────────────────────────────────

    def _h(self):
        """Return Authorization header."""
        return {"Authorization": f"Bearer {self.token}"}

    def _login(self, email, password, role):
        """POST /api/auth/login/ and store tokens. Returns True on success."""
        with self.client.post(
            "/api/auth/login/",
            json={"email": email, "password": password, "role": role},
            catch_response=True,
            name=f"[M1] POST /api/auth/login/ ({role})",
        ) as res:
            if res.status_code == 200:
                data = res.json()
                self.token      = data.get("token")
                self.refresh_tk = data.get("refresh")
                res.success()
                return True
            res.failure(f"Login failed {res.status_code}")
            return False

    def _discover_ai_data(self, class_ids):
        """
        For every class in class_ids, fetch AI courses and populate:
          self.course_ids, self.anim_ids, self.quiz_course_ids
        """
        self.course_ids      = []
        self.anim_ids        = []
        self.quiz_course_ids = []

        for cid in class_ids:
            r = self.client.get(
                f"/api/ai-courses/class/{cid}/",
                headers=self._h(),
                name="[M3] GET /api/ai-courses/class/<id>/ [setup]",
            )
            if r.status_code != 200:
                continue
            for course in r.json():
                if course.get("status") != "READY":
                    continue
                course_id = course["id"]
                self.course_ids.append(course_id)

                # animations
                ra = self.client.get(
                    f"/api/ai-courses/{course_id}/animations/list/",
                    headers=self._h(),
                    name="[M5] GET /api/ai-courses/<id>/animations/list/ [setup]",
                )
                if ra.status_code == 200:
                    self.anim_ids.extend(a["id"] for a in ra.json())

                # quiz
                rq = self.client.get(
                    f"/api/ai-courses/{course_id}/quiz/status/",
                    headers=self._h(),
                    name="[M6] GET /api/ai-courses/<id>/quiz/status/ [setup]",
                )
                if rq.status_code == 200 and rq.json().get("status") == "READY":
                    self.quiz_course_ids.append(course_id)
