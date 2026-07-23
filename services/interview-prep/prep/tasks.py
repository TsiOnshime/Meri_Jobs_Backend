"""Celery tasks -- async answer evaluation runs here, not inline in a request.

Mirrors cv-parser's pattern: the view returns 202 immediately, this task
does the slow LLM call in the background, and the client polls
GET /interview/answer/{answer_id} for the result.

Only ever queued for open_ended answers. multiple_choice answers are graded
synchronously in the view (selected_option == correct_option) since that's
deterministic and doesn't need an LLM call.
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
        answer = Answer.objects.select_related("question", "question__session").get(
            id=answer_id
        )
    except Answer.DoesNotExist:
        # Nothing sensible to retry -- the row is just gone.
        return

    if answer.question.question_type != "open_ended":
        # Defensive: this task should only ever be queued for open_ended
        # answers. If it lands here for a multiple_choice answer, something
        # upstream queued it by mistake -- don't burn an LLM call on it.
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

    _mark_session_complete_if_done(answer.question.session)


def _mark_session_complete_if_done(session):
    """Flip InterviewSession.status once every round has a completed answer.

    session.status is a stored field (unlike rounds_completed/is_complete,
    which are computed on the fly), so something has to be the one place
    that actually writes "completed" to it. This task is that place for
    open_ended rounds; the view's synchronous multiple_choice grading path
    needs to call the same check after it grades an answer.
    """
    if session.status == "completed":
        return
    if session.rounds_completed >= session.total_rounds:
        session.status = "completed"
        session.save(update_fields=["status"])