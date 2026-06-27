"""Module 4 — RAG tasks."""
import random

_QUESTIONS = [
    "What is a binary search tree?",
    "Explain the quicksort algorithm.",
    "How does dynamic programming work?",
    "What are the differences between BFS and DFS?",
    "Explain time complexity and Big-O notation.",
    "What is a hash table and how does it handle collisions?",
    "Describe merge sort and its complexity.",
    "What are stacks and queues used for?",
]


def ask_question(user):
    if not user.course_ids:
        return
    user.client.post(
        f"/api/ai-courses/{random.choice(user.course_ids)}/ask/",
        json={"question": random.choice(_QUESTIONS)},
        headers=user._h(),
        name="[M4] POST /api/ai-courses/<id>/ask/",
    )


def reformulate_answer(user):
    if not user.course_ids:
        return
    user.client.post(
        f"/api/ai-courses/{random.choice(user.course_ids)}/reformulate/",
        json={
            "question": random.choice(_QUESTIONS),
            "previous_answer": "This is a complex explanation that needs simplification.",
        },
        headers=user._h(),
        name="[M4] POST /api/ai-courses/<id>/reformulate/",
    )


TASKS = {ask_question: 4, reformulate_answer: 2}
