import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from confluent_kafka import Consumer

from matching.consumers.cv_parsed_consumer import handle_cv_parsed
from matching.consumers.job_ingested_consumer import handle_job_ingested

logger = logging.getLogger(__name__)

TOPICS = ["cv.parsed", "job.ingested"]

HANDLERS = {
    "cv.parsed": handle_cv_parsed,
    "job.ingested": handle_job_ingested
}

class Command(BaseCommand):
    help = "Consumes cv.parsed and job.ingested events and runs the matching pipeline"
    
    def handle(self, *args, **options):
        consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BROKER_URL, 
            "group.id": "matching-engine-group", 
            "auto.offset.reset": "earliest"
        })
        
        consumer.subscribe(TOPICS)
        
        self.stdout.write(self.style.SUCCESS(f"Listening on topics: {TOPICS}"))
        
        try: 
            while True:
                msg = consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    self.stderr.write(self.style.ERROR(f"Kafka error: {msg.error()}"))
                    continue
                # if msg.error():
                #     logger.error("kafka_consume_error", extra={"error": str(msg.error())})
                #     continue
                self._process_message(msg)
        except KeyboardInterrupt:
            self.stdout.write("Shutting down consumer...")
        finally:
            consumer.close()
    def _process_message(self, msg):
        topic = msg.topic()
        handler = HANDLERS.get(topic)
        
        if handler is None:
            logger.warning("no_handler_for_topic", extra={"topic": topic})
        try: 
            event = json.loads(msg.value())
            handler(event)
        except Exception:
            logger.exception(
                "event_processing_failed", 
                extra={"topic": topic, "raw_value": msg.value()}
            )