"""Module 6 — Quiz tasks."""
import random

QUIZ_QUESTION_COUNT = 20
QUIZ_OPTION_COUNT   = 4


# ── Student tasks ─────────────────────────────────────────────────────────────

def quiz_status(user):
    if not user.course_ids:
        return
    user.client.get(
        f"/api/ai-courses/{random.choice(user.course_ids)}/quiz/status/",
        headers=user._h(),
        name="[M6] GET /api/ai-courses/<id>/quiz/status/",
    )


def quiz_questions(user):
    if not user.quiz_course_ids:
        return
    user.client.get(
        f"/api/ai-courses/{random.choice(user.quiz_course_ids)}/quiz/questions/",
        headers=user._h(),
        name="[M6] GET /api/ai-courses/<id>/quiz/questions/",
    )


def submit_quiz_attempt(user):
    if not user.quiz_course_ids:
        return
    answers = [random.randint(0, QUIZ_OPTION_COUNT - 1) for _ in range(QUIZ_QUESTION_COUNT)]
    user.client.post(
        f"/api/ai-courses/{random.choice(user.quiz_course_ids)}/quiz/attempt/",
        json={"answers": answers},
        headers=user._h(),
        name="[M6] POST /api/ai-courses/<id>/quiz/attempt/",
    )


STUDENT_TASKS = {quiz_status: 4, quiz_questions: 3, submit_quiz_attempt: 2}


# ── Teacher tasks ─────────────────────────────────────────────────────────────

def quiz_results(user):
    if not user.quiz_course_ids or not user.class_id:
        return
    user.client.get(
        f"/api/teacher/classes/{user.class_id}/ai-courses/{random.choice(user.quiz_course_ids)}/quiz-results/",
        headers=user._h(),
        name="[M6] GET /api/teacher/.../quiz-results/",
    )


TEACHER_TASKS = {quiz_results: 2}
