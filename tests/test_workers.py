import pytest
import asyncio
from app.workers import stale_sensor_monitor, sensor_snapshot_consumer

@pytest.mark.asyncio
async def test_monitor_lifecycle():
    stale_sensor_monitor.start_monitor()
    assert stale_sensor_monitor._monitor_task is not None
    await stale_sensor_monitor.stop_monitor()
    
@pytest.mark.asyncio
async def test_consumer_lifecycle(monkeypatch):
    from aiokafka import AIOKafkaConsumer
    
    class MockConsumer:
        def __init__(self, *args, **kwargs):
            pass
        async def start(self):
            pass
        async def stop(self):
            pass
        def __aiter__(self):
            return self
        async def __anext__(self):
            raise StopAsyncIteration
            
    monkeypatch.setattr(sensor_snapshot_consumer, "AIOKafkaConsumer", MockConsumer)
    
    await sensor_snapshot_consumer.start_consumer()
    # Let event loop switch to run the task briefly
    await asyncio.sleep(0.1)
    await sensor_snapshot_consumer.stop_consumer()
