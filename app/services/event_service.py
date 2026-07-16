import logging
from typing import Optional

from app.config.database import AsyncSessionLocal
from app.models.fusion_event import FusionEvent
from app.services.kafka_service import kafka_service

logger = logging.getLogger(__name__)


class EventService:
    async def publish_and_store_event(
        self, robot_id: str, event_type: str, severity: str, confidence: float, data: Optional[dict] = None
    ):
        logger.info(f"Emitting {event_type} for robot {robot_id}")

        # 1. Publish to Kafka
        event_payload = {
            "robot_id": robot_id,
            "event_type": event_type,
            "severity": severity,
            "confidence": confidence,
            "data": data or {},
        }
        await kafka_service.publish_event(event_type, event_payload)

        # 2. Store in DB
        try:
            async with AsyncSessionLocal() as db:
                db_event = FusionEvent(
                    robot_id=robot_id,
                    event_type=event_type,
                    severity=severity,
                    confidence=confidence,
                    data=data,
                )
                db.add(db_event)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to store event in DB: {e}")


event_service = EventService()
