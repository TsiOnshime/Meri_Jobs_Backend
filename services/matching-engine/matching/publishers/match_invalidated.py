import json
import logging 
from datetime import datetime, timezone
from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__name__)

_producer = Producer({"bootstrap.servers": settings.KAFKA_BROKER_URL})

TOPIC = "match.invalidated"

def _delivery_callback(err, msg):
    if err is not None:
        logger.error(
            "kafka_delivery_failed", 
            extra={"topic": msg.topic(), "error": str(err)}
        )
        
def publish_match_invalidated(cv_id, job_id, reason: str) -> None:
    payload = {
        "event": "match.invalidated",
        "cv_id": str(cv_id),
        "job_id": str(job_id), 
        "reason": reason,
        "invalidated_at": datetime.now(timezone.utc).isoformat()
    }
    
    _producer.produce(
        TOPIC,
        key=str(cv_id),
        value=json.dumps(payload),
        callback=_delivery_callback
    )
    
    _producer.poll(0)