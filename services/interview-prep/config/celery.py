"""
Celery app for the interview-prep service.

This is celery *within* this one service (background answer evaluation) --
not to be confused with Kafka, which is how services talk to each other.
Same split as cv-parser: Kafka = cross-service events, Celery = this
service's own slow background jobs.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("interview_prep")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()