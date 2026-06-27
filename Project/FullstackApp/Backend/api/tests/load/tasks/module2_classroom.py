"""Module 2 — Classroom & Assignment tasks."""
import random


# ── Student tasks ─────────────────────────────────────────────────────────────

def list_classes(user):
    user.client.get("/api/classes/", headers=user._h(), name="[M2] GET /api/classes/")


def class_detail(user):
    if not user.class_ids:
        return
    user.client.get(
        f"/api/classes/{random.choice(user.class_ids)}/",
        headers=user._h(),
        name="[M2] GET /api/classes/<id>/",
    )


def list_assignments(user):
    user.client.get("/api/assignments/", headers=user._h(), name="[M2] GET /api/assignments/")


def account_stats(user):
    user.client.get("/api/account/stats/", headers=user._h(), name="[M2] GET /api/account/stats/")


STUDENT_TASKS = {list_classes: 7, class_detail: 5, list_assignments: 6, account_stats: 3}


# ── Teacher tasks ─────────────────────────────────────────────────────────────

def list_teacher_classes(user):
    user.client.get("/api/teacher/classes/", headers=user._h(), name="[M2] GET /api/teacher/classes/")


def teacher_class_detail(user):
    if not user.class_id:
        return
    user.client.get(
        f"/api/teacher/classes/{user.class_id}/",
        headers=user._h(),
        name="[M2] GET /api/teacher/classes/<id>/",
    )


def teacher_stats(user):
    user.client.get("/api/teacher/stats/", headers=user._h(), name="[M2] GET /api/teacher/stats/")


def teacher_students(user):
    user.client.get("/api/teacher/students/", headers=user._h(), name="[M2] GET /api/teacher/students/")


TEACHER_TASKS = {list_teacher_classes: 6, teacher_class_detail: 4, teacher_stats: 2, teacher_students: 2}
