"""Celery tasks -- async CV parsing runs here, not inline in a request."""
import logging
import os

from celery import shared_task
from django.conf import settings

from .ai.llm_suggestions import get_llm_suggestions_and_clarity
from .extraction import get_parser
from .models import CV, CVScore, CVSuggestion, ParsedCV, ParseFailureLog
from .publishers.cv_parsed import publish
from .scoring import compute_confidence, compute_cv_score
from .suggestions.keywords import generate_suggestions

logger = logging.getLogger(__name__)


def _cleanup_file(path):
    """Delete the uploaded file once it's no longer needed -- raw_text is
    already saved in the database by the time this is called, so the
    original file itself doesn't need to persist on disk afterward."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning("Could not delete uploaded file %s: %s", path, exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def parse_cv_task(self, cv_id):
    try:
        cv = CV.objects.get(id=cv_id)
    except CV.DoesNotExist:
        logger.error("parse_cv_task: CV %s not found", cv_id)
        return

    cv.status = CV.Status.PROCESSING
    cv.save(update_fields=["status", "updated_at"])

    try:
        parser_module = get_parser(cv.file_type)
        fields = parser_module.parse(cv.storage_path)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        ParseFailureLog.objects.create(
            cv=cv, error_type=type(exc).__name__, error_detail=str(exc),
        )
        cv.status = CV.Status.FAILED
        cv.save(update_fields=["status", "updated_at"])
        _cleanup_file(cv.storage_path)
        return

    _cleanup_file(cv.storage_path)  # parsed successfully -- don't need the file anymore

    confidence, flagged_sections = compute_confidence(fields)

    parsed_cv, _ = ParsedCV.objects.update_or_create(
        cv=cv,
        defaults={
            "name": fields.get("name", ""),
            "email": fields.get("email", ""),
            "phone": fields.get("phone", ""),
            "professional_summary": fields.get("professional_summary") or None,
            "education": fields.get("education", []),
            "experience": fields.get("experience", []),
            "skills": fields.get("skills", []),
            "certifications": fields.get("certifications", []),
            "raw_text": fields.get("raw_text", ""),
            "confidence_score": confidence,
            "flagged_sections": flagged_sections,
        },
    )

    # --- Suggestions + clarity + experience/role: try the LLM first,
    # fall back to rule-based logic if it's disabled/unavailable/errors.
    llm_result = get_llm_suggestions_and_clarity(fields.get("raw_text", ""))

    if llm_result:
        suggestions, clarity_score, experience_years, role_category = llm_result

        for s in suggestions:
            CVSuggestion.objects.create(cv=cv, **s)

        score = compute_cv_score(fields, clarity_override=clarity_score)

        parsed_cv.experience_years = experience_years
        parsed_cv.role_category = role_category
        parsed_cv.save(update_fields=["experience_years", "role_category"])

        logger.info("cv_id=%s used LLM-generated suggestions + clarity", cv.id)
    else:
        for s in generate_suggestions(fields):
            CVSuggestion.objects.create(cv=cv, **s)

        score = compute_cv_score(fields)
        logger.info("cv_id=%s used rule-based suggestions + clarity (LLM unavailable)", cv.id)

    CVScore.objects.update_or_create(cv=cv, defaults=score)

    if confidence < settings.CV_CONFIDENCE_THRESHOLD:
        cv.status = CV.Status.NEEDS_REVIEW
        cv.save(update_fields=["status", "updated_at"])
        logger.info(
            "cv_id=%s needs_review (confidence=%.2f, flagged=%s) -- event NOT published",
            cv.id, confidence, flagged_sections,
        )
        return

    cv.status = CV.Status.COMPLETE
    cv.save(update_fields=["status", "updated_at"])
    publish(cv, parsed_cv)