import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer
from prometheus_client import Counter

from app.config.settings import settings
from app.schemas.sensor_snapshot import SensorSnapshot
from app.services.fusion_service import fusion_service

logger = logging.getLogger(__name__)

snapshots_received = Counter("rex_fusion_snapshots_received_total", "Total snapshots received")
snapshots_invalid = Counter("rex_fusion_snapshots_invalid_total", "Invalid snapshots received")

_consumer_task: Optional[asyncio.Task] = None
_consumer: AIOKafkaConsumer = None


async def consume():
    global _consumer
    try:
        _consumer = AIOKafkaConsumer(
            settings.KAFKA_INPUT_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id=f"{settings.KAFKA_CLIENT_ID}-consumer",
            group_id=settings.KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        await _consumer.start()
        logger.info(f"Started Kafka consumer on topic {settings.KAFKA_INPUT_TOPIC}")

        async for msg in _consumer:
            snapshots_received.inc()
            try:
                snapshot = SensorSnapshot(**msg.value)
                await fusion_service.process_snapshot(snapshot)
            except Exception as e:
                snapshots_invalid.inc()
                logger.error(f"Failed to process snapshot: {e}")
    except asyncio.CancelledError:
        logger.info("Kafka consumer cancelled")
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")
    finally:
        if _consumer:
            await _consumer.stop()
            logger.info("Kafka consumer stopped")


async def start_consumer():
    global _consumer_task
    _consumer_task = asyncio.create_task(consume())


async def stop_consumer():
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
