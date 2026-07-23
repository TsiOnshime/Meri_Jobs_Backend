"""Celery tasks -- async answer evaluation runs here, not inline in a request.

Mirrors cv-parser's pattern: the view returns 202 immediately, this task
does the slow LLM call in the background, and the client polls
GET /interview/answer/{answer_id} for the result.
"""
from celery import shared_task
from django.utils import timezone

from .models import Answer


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def evaluate_answer(self, answer_id):
    # Imported here rather than at module level: keeps the LLM client/SDK
    # import (and its API key requirement) out of the task-registration
    # path, same reasoning as generation/ being isolated from views.py.
    from .generation.feedback import generate_feedback

    try:
        answer = Answer.objects.select_related("question").get(id=answer_id)
    except Answer.DoesNotExist:
        # Nothing sensible to retry -- the row is just gone.
        return

    try:
        result = generate_feedback(
            question_text=answer.question.text,
            answer_text=answer.answer_text,
        )
    except Exception as exc:
        answer.status = "failed"
        answer.save(update_fields=["status"])
        raise self.retry(exc=exc)

    answer.score = result["score"]
    answer.strengths = result["strengths"]
    answer.improvements = result["improvements"]
    answer.suggested_answer = result["suggested_answer"]
    answer.status = "completed"
    answer.completed_at = timezone.now()
    answer.save(
        update_fields=[
            "score",
            "strengths",
            "improvements",
            "suggested_answer",
            "status",
            "completed_at",
        ]
    )