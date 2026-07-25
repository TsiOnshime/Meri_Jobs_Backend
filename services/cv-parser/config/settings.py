from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-secret-key-change-me")
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_spectacular",
    "parser",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# --- Database Setup (Defaults to SQLite for easy local testing) ---
if config("USE_SQLITE", default=True, cast=bool):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="merijobs"),
            "USER": config("POSTGRES_USER", default="merijobs"),
            "PASSWORD": config("POSTGRES_PASSWORD", default="changeme"),
            "HOST": config("POSTGRES_HOST", default="postgres"),
            "PORT": config("POSTGRES_PORT", default="5432"),
        }
    }

REDIS_HOST = config("REDIS_HOST", default="redis")
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)
KAFKA_BROKER_URL = config("KAFKA_BROKER_URL", default="kafka:9092")
KAFKA_CV_PARSED_TOPIC = config("KAFKA_CV_PARSED_TOPIC", default="cv.parsed")

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "parser.authentication.InternalTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Internal auth (Updated!) ---
INTERNAL_SHARED_TOKEN = config("INTERNAL_SHARED_TOKEN", default="internal-token-change-me")

# --- Celery ---
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_ALWAYS_EAGER = config("CELERY_EAGER", default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

MEDIA_ROOT = config("CV_STORAGE_ROOT", default=str(BASE_DIR / "uploaded_cvs"))
MAX_UPLOAD_SIZE_BYTES = config("MAX_UPLOAD_SIZE_BYTES", default=10 * 1024 * 1024, cast=int)
CV_CONFIDENCE_THRESHOLD = config("CV_CONFIDENCE_THRESHOLD", default=0.7, cast=float)
import os
# --- Optional LLM layer (suggestions + clarity scoring) ------------------
# Decoupled on purpose -- if GROQ_API_KEY is blank or LLM_ENABLED=false,
# cv-parser still fully works using the rule-based logic in scoring.py /
# suggestions/keywords.py. Never a hard dependency.
# Groq's API is OpenAI-compatible, so we reuse the `openai` client library
# pointed at Groq's base_url instead of OpenAI's.
LLM_ENABLED = config("LLM_ENABLED", default=True, cast=bool)
GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_BASE_URL = config("GROQ_BASE_URL", default="https://api.groq.com/openai/v1")
LLM_MODEL = config("LLM_MODEL", default="llama-3.3-70b-versatile")
LLM_TIMEOUT_SECONDS = config("LLM_TIMEOUT_SECONDS", default=8, cast=int)