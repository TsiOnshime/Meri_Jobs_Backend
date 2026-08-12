"""
Django settings for the api-gateway service.
Config comes from environment variables (see .env.example at repo root).
"""
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
    "gateway",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "gateway.middleware.correlation.CorrelationMiddleware",
    "gateway.middleware.jwt_auth.JWTAuthenticationMiddleware",
    "gateway.middleware.rate_limit.RateLimitMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"

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

# Internal service URLs
CV_PARSER_URL = config("CV_PARSER_URL", default="http://cv-parser:8001")
MATCHING_ENGINE_URL = config("MATCHING_ENGINE_URL", default="http://matching-engine:8002")
JOB_INGESTION_URL = config("JOB_INGESTION_URL", default="http://job-ingestion:8003")
INTERVIEW_PREP_URL = config("INTERVIEW_PREP_URL", default="http://interview-prep:8004")
USERS_URL = config("USERS_URL", default="http://users:8005")

# Internal token for service-to-service communication
INTERNAL_TOKEN = config("INTERNAL_TOKEN", default="internal-token-change-me")

# JWT Configuration
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default=SECRET_KEY)
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS256")
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60, cast=int)
JWT_REFRESH_TOKEN_LIFETIME_DAYS = config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)

# CORS configuration
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000,http://localhost:8000").split(",")

# Rate limiting configuration
CIRCUIT_BREAKER_THRESHOLD = config("CIRCUIT_BREAKER_THRESHOLD", default=5, cast=int)
CIRCUIT_BREAKER_TIMEOUT = config("CIRCUIT_BREAKER_TIMEOUT", default=60, cast=int)
REQUEST_TIMEOUT = config("REQUEST_TIMEOUT", default=30, cast=int)

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "gateway.handlers.custom_exception_handler",
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
