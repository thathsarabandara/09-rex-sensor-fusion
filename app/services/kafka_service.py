import json
import logging

from aiokafka import AIOKafkaProducer

from app.config.settings import settings

logger = logging.getLogger(__name__)


class KafkaService:
    def __init__(self):
        self.producer = None
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.client_id = settings.KAFKA_CLIENT_ID
        self.fused_topic = settings.KAFKA_FUSED_STATE_TOPIC

    async def start(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retry_backoff_ms=500,
                request_timeout_ms=10000,
            )
            await self.producer.start()
            logger.info("Kafka Producer started")
        except Exception as e:
            logger.error(f"Failed to start Kafka Producer: {e}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer stopped")

    async def publish_fused_state(self, state_dict: dict):
        if not self.producer:
            return
        try:
            await self.producer.send_and_wait(self.fused_topic, state_dict)
        except Exception as e:
            logger.error(f"Failed to publish fused state: {e}")

    async def publish_event(self, event_type: str, event_data: dict):
        if not self.producer:
            return
        topic = f"rex.sensor-fusion.{event_type.lower().replace('_', '-')}.v1"
        try:
            await self.producer.send_and_wait(topic, event_data)
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")


kafka_service = KafkaService()
