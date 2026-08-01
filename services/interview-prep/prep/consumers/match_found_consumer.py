"""Consumes match.found -- pre-generates mock questions for the job.

Runs as its own long-lived process via `python manage.py
consume_match_found` (see prep/management/commands/consume_match_found.py),
separate from the Django request/response cycle and separate from the
Celery worker. Kafka = cross-service events, Celery = this service's own
background jobs -- same split config/celery.py already documents.

Best-effort cache warm only: if this consumer is down, lagging, or a
given job_id was never matched, create_session() in views.py just falls
back to a live generate_questions() call. Nothing here is load-bearing
for correctness.
"""
import json
import logging

from confluent_kafka import Consumer, KafkaError
from django.conf import settings

logger = logging.getLogger(__name__)

TOPIC = "match.found"
GROUP_ID = "interview-prep.match-found-consumer"


def _build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.KAFKA_BROKER_URL,
            "group.id": GROUP_ID,
            # Manual commits: only advance the offset after the question
            # set is actually cached, so a crash mid-generation replays
            # the event instead of silently dropping the pre-generation.
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
        }
    )


def _handle_message(payload: dict) -> None:
    """Pre-generate and cache a question set for one match.found event.

    Expected payload shape: {"job_id": <uuid str>, "job_title": <str>,
    "focus_area": <str, optional>}. Missing/malformed fields are logged
    and skipped rather than raised -- this is a cache warm, never
    something a session creation should block on.
    """
    # Imported here rather than at module level, same reasoning as
    # views.py/tasks.py: keeps the Gemini SDK/API-key requirement out of
    # this module's import path until a message actually needs it.
    from ..generation.job_cache import set_cached_questions
    from ..generation.questions import generate_questions

    job_id = payload.get("job_id")
    job_title = payload.get("job_title", "") or ""
    focus_area = payload.get("focus_area", "") or ""

    if not job_id:
        logger.warning("match.found event missing job_id, skipping: %r", payload)
        return

    try:
        questions = generate_questions(
            job_title=job_title, focus_area=focus_area, count=10
        )
    except Exception:
        logger.exception(
            "Failed to pre-generate questions for job_id=%s -- the "
            "candidate's session will just fall back to a live "
            "generate_questions() call instead of hitting this cache.",
            job_id,
        )
        return

    set_cached_questions(job_id, focus_area, questions)
    logger.info("Pre-generated and cached questions for job_id=%s", job_id)


def run() -> None:
    """Blocking poll loop -- intended to be the entire body of a long-lived process."""
    consumer = _build_consumer()
    consumer.subscribe([TOPIC])
    logger.info("match_found_consumer listening on topic=%s", TOPIC)

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Kafka consumer error: %s", msg.error())
                continue

            try:
                payload = json.loads(msg.value())
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Skipping unparseable match.found message: %r", msg.value()
                )
                consumer.commit(msg)
                continue

            _handle_message(payload)
            consumer.commit(msg)
    finally:
        consumer.close()