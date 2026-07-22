from confluent_kafka import Producer
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Kafka producer for publishing events.
    """
    
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': settings.KAFKA_BROKER_URL,
            'client.id': 'api-gateway'
        })
    
    def publish_event(self, topic, event_data):
        """
        Publish an event to Kafka.
        
        Args:
            topic: Kafka topic name
            event_data: Dictionary containing event data
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in event_data:
                from datetime import datetime
                event_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Serialize to JSON
            message = json.dumps(event_data).encode('utf-8')
            
            # Publish to Kafka
            self.producer.produce(
                topic,
                value=message,
                callback=self._delivery_report
            )
            
            # Flush to ensure message is sent
            self.producer.flush(timeout=5)
            
            logger.info(f"Published event to {topic}: {event_data.get('event', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            return False
    
    def _delivery_report(self, err, msg):
        """
        Callback for Kafka delivery report.
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def publish_user_registered(self, user_id, email, name):
        """Publish user registered event"""
        event = {
            'event': 'user.registered',
            'user_id': str(user_id),
            'email': email,
            'name': name
        }
        return self.publish_event('user-events', event)
    
    def publish_cv_uploaded(self, user_id, cv_id, file_name):
        """Publish CV uploaded event"""
        event = {
            'event': 'cv.uploaded',
            'user_id': str(user_id),
            'cv_id': str(cv_id),
            'file_name': file_name
        }
        return self.publish_event('cv-events', event)
    
    def publish_match_requested(self, user_id, cv_id):
        """Publish match requested event"""
        event = {
            'event': 'match.requested',
            'user_id': str(user_id),
            'cv_id': str(cv_id)
        }
        return self.publish_event('match-events', event)
