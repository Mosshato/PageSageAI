"""Module 1 — Authentication tasks."""
import random


def get_me(user):
    user.client.get("/api/auth/me/", headers=user._h(), name="[M1] GET /api/auth/me/")


def refresh_token(user):
    if not user.refresh_tk:
        return
    with user.client.post(
        "/api/auth/token/refresh/",
        json={"refresh": user.refresh_tk},
        catch_response=True,
        name="[M1] POST /api/auth/token/refresh/",
    ) as res:
        if res.status_code == 200:
            user.token = res.json().get("access", user.token)
            res.success()


TASKS = {get_me: 4, refresh_token: 1}
