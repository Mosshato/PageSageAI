"""Module 3 — PDF Pipeline tasks."""
import random


def list_ai_courses(user):
    if not user.class_ids:
        return
    user.client.get(
        f"/api/ai-courses/class/{random.choice(user.class_ids)}/",
        headers=user._h(),
        name="[M3] GET /api/ai-courses/class/<id>/",
    )


def ai_course_status(user):
    if not user.course_ids:
        return
    user.client.get(
        f"/api/ai-courses/{random.choice(user.course_ids)}/status/",
        headers=user._h(),
        name="[M3] GET /api/ai-courses/<id>/status/",
    )


def ai_course_page(user):
    if not user.course_ids:
        return
    user.client.get(
        f"/api/ai-courses/{random.choice(user.course_ids)}/page/{random.randint(1, 3)}/",
        headers=user._h(),
        name="[M3] GET /api/ai-courses/<id>/page/<n>/",
    )


TASKS = {list_ai_courses: 5, ai_course_status: 3, ai_course_page: 2}
