"""
Makes sure the Celery app is loaded whenever Django starts, so that
shared_task-decorated tasks in prep/tasks.py get registered.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)