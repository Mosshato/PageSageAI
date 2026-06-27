"""
Logica de auth a fost mutata in apps/authentication/. Acest fisier ramane
doar ca re-export, ca importurile vechi (api.views.auth_views) sa nu se rupa.
"""
from apps.authentication.views import signup, login, me, user_payload, tokens_for_user  # noqa: F401
