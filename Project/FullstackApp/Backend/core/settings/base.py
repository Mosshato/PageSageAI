"""
Setari comune intre toate mediile (local + production).
Mediile specifice (local.py / production.py) fac `from .base import *`
si suprascriu/adauga ce difera (SECRET_KEY, DEBUG, DATABASES, CORS, ...).
"""

from datetime import timedelta
from pathlib import Path

# core/settings/base.py -> core/settings/ -> core/ -> Backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'api',
]

# Ii spunem lui Django sa foloseasca User-ul nostru custom in loc de auth.User
AUTH_USER_MODEL = 'api.User'

# Configurare Django REST Framework — toate endpoint-urile cer JWT by default
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# Configurare token JWT — acelasi comportament ca in Node.js
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),   # token expira dupa 5 minute
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),      # refresh token (nu il folosim in frontend acum)
    'ROTATE_REFRESH_TOKENS': False,
    'AUTH_HEADER_TYPES': ('Bearer',),                 # header: Authorization: Bearer <token>
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # must be FIRST
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# AI pipelines — modele LLM si parametri RAG/embeddings.
# Identice in local si production, de aceea stau in base.py (nu se citesc
# din .env — nu sunt secrete, sunt config de aplicatie).
# Folosite de api/ai_pipeline.py, api/manim_pipeline.py, api/quiz_pipeline.py.

RAG_LLM_MODEL = "gemini-2.5-flash"
RAG_LLM_TEMPERATURE = 0.3
RAG_TOP_K = 4

QUIZ_LLM_MODEL = "gemini-3.5-flash"
QUIZ_LLM_TEMPERATURE = 0.3

MANIM_LLM_MODEL = "gemini-3.5-flash"
MANIM_LLM_TEMPERATURE = 0.2

EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"
RAG_CHUNK_SIZE = 700
RAG_CHUNK_OVERLAP = 100

# Functionalities/ e un proiect separat (alt venv), dar ai_pipeline.py ii
# importa scripturile dinamic (sys.path) si foloseste ChromaDB-ul lui comun.
# Centralizat aici ca MEDIA_ROOT — un singur loc de adevar pentru cale.
FUNCTIONALITIES_ROOT = BASE_DIR.parent.parent / "Functionalities"
OSSU_CHROMA_DIR = str(FUNCTIONALITIES_ROOT / "RAG" / "chroma_ossu_db")
