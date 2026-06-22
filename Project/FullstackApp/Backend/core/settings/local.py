"""
Setari pentru development local.
Activat implicit (cand ENV_NAME != 'production').
"""

import os

from dotenv import load_dotenv

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-doar-local')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite's default dev port
]

# AI / third-party service keys — citite aici o singura data si expuse prin
# settings.<KEY>; api/ai_pipeline.py, api/manim_pipeline.py si
# api/quiz_pipeline.py le citesc din settings, nu mai fac load_dotenv singure.
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_API_KEY_MANIM = os.environ['GEMINI_API_KEY_MANIM']
DEEPGRAM_API_KEY = os.environ['DEEPGRAM_API_KEY']
