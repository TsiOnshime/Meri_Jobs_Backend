"""Celery app for cv-parser. Loaded automatically via config/__init__.py."""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("cv_parser_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()