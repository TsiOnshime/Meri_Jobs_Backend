"""Builds and publishes the cv.parsed event once extraction succeeds.

Schema matches the event contract shared with matching-engine:
    CV.Parsed: {
        event: "cv.parsed", cv_id: UUID, raw_skills: [],
        experience_years: int, seniority: varchar,
        role_category: varchar, timestamp: datetime
    }
"""
import json
import logging
from datetime import datetime, timezone

from django.conf import settings

logger = logging.getLogger(__name__)


def _infer_seniority(years: int) -> str:
    if years >= 8:
        return "senior"
    if years >= 3:
        return "mid"
    return "junior"


def build_event(cv, parsed_cv) -> dict:
    # Pulling real AI-calculated values directly from the database
    years = getattr(parsed_cv, "experience_years", 0) 
    role = getattr(parsed_cv, "role_category", "unspecified")

    return {
        "event": "cv.parsed",
        "cv_id": str(cv.id),
        "raw_skills": parsed_cv.skills,
        "experience_years": years,
        "seniority": _infer_seniority(years),
        "role_category": role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publish(cv, parsed_cv):
    """Publish to Kafka via confluent-kafka. Falls back to a log line if
    Kafka/Docker isn't running yet, so local dev doesn't hard-fail here."""
    event = build_event(cv, parsed_cv)
    payload = json.dumps(event).encode("utf-8")

    try:
        from confluent_kafka import Producer

        producer = Producer({"bootstrap.servers": settings.KAFKA_BROKER_URL})
        producer.produce(settings.KAFKA_CV_PARSED_TOPIC, value=payload)
        producer.flush(timeout=5)
        logger.info("Published cv.parsed for cv_id=%s", cv.id)
    except Exception:
        logger.warning(
            "Kafka unavailable -- cv.parsed NOT published for cv_id=%s. "
            "Payload was: %s", cv.id, event,
        )
    return event