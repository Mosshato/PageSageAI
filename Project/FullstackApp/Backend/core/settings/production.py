"""
Setari pentru productie.
Activat cu variabila de mediu ENV_NAME=production.
Toate valorile sensibile sunt OBLIGATORII (fara default-uri) — daca lipsesc,
serverul trebuie sa pice la pornire, nu sa ruleze cu valori implicite nesigure.
"""

import os

from .base import *  # noqa: F401,F403

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

CORS_ALLOWED_ORIGINS = os.environ['CORS_ALLOWED_ORIGINS'].split(',')

# AI / third-party service keys — vezi local.py pentru explicatie
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_API_KEY_MANIM = os.environ['GEMINI_API_KEY_MANIM']
DEEPGRAM_API_KEY = os.environ['DEEPGRAM_API_KEY']

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
