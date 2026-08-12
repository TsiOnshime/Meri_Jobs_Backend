"""Builds and publishes match.found, once per qualifying candidate."""

import json
import logging
from datetime import datetime, timezone
from confluent_kafka import Producer
from django.conf import settings

from matching.models import CV, Job

logger = logging.getLogger(__name__)

_producer = Producer({"bootstrap.servers": settings.KAFKA_BROKER_URL})

TOPIC = "match.found"

def _delivery_callback(err, msg):
    if err is not None:
        logger.error(
            "kafka_delivery_failed", 
            extra={"topic": msg.topic(), "error": str(err)}
        )


def publish_match_found(cv: CV, job: Job, overall_score: int, breakdown: dict) -> None:
    payload = {
        "event": "match.found", 
        "cv_id": str(cv.cv_id), 
        "job_id": str(job.job_id),
        "overall_score": overall_score, 
        "source_url": job.source_url,
        "breakdown": breakdown, 
        "computed_at": datetime.now(timezone.utc).isoformat()
    }
    
    _producer.produce(
        TOPIC,
        key=str(cv.cv_id), 
        value=json.dumps(payload),
        callback=_delivery_callback
    )
    
    _producer.poll(0)