"""Module 5 — Animation tasks."""
import random

_CONCEPTS = [
    "Binary Search Tree", "Quicksort Algorithm", "Dijkstra Shortest Path",
    "Dynamic Programming", "Hash Table", "Merge Sort", "Stack and Queue",
]


def list_animations(user):
    if not user.course_ids:
        return
    user.client.get(
        f"/api/ai-courses/{random.choice(user.course_ids)}/animations/list/",
        headers=user._h(),
        name="[M5] GET /api/ai-courses/<id>/animations/list/",
    )


def animation_status(user):
    if not user.anim_ids:
        return
    user.client.get(
        f"/api/animations/{random.choice(user.anim_ids)}/status/",
        headers=user._h(),
        name="[M5] GET /api/animations/<id>/status/",
    )


def request_animation(user):
    if not user.course_ids:
        return
    cid = random.choice(user.course_ids)
    with user.client.post(
        f"/api/ai-courses/{cid}/animations/",
        json={"concept": random.choice(_CONCEPTS)},
        headers=user._h(),
        catch_response=True,
        name="[M5] POST /api/ai-courses/<id>/animations/",
    ) as res:
        if res.status_code in (200, 201):
            anim_id = res.json().get("animation_id")
            if anim_id and anim_id not in user.anim_ids:
                user.anim_ids.append(anim_id)
            res.success()


TASKS = {list_animations: 4, animation_status: 3, request_animation: 2}
