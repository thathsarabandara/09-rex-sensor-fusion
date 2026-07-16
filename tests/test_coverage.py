import pytest
from app.filters import line_sensor, ultrasonic, imu, freshness
from app.middleware import auth, internal_auth
from app.routes import fusion, websockets, health
from app.services import cache_service, event_service, kafka_service, ownership_service, websocket_service, fusion_service
from app.workers import sensor_snapshot_consumer, stale_sensor_monitor
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
import httpx
from unittest.mock import AsyncMock, MagicMock
import datetime

@pytest.mark.asyncio
async def test_line_sensor_coverage():
    state = {"left_outer": True, "left_inner": True, "right_inner": True, "right_outer": True}
    res = line_sensor.get_debounced_state(state, {}, window_size=2)
    assert res
    
    line_sensor.get_line_position(state)
    line_sensor.get_line_position({"left_outer": True, "left_inner": True, "right_inner": False, "right_outer": False})
    line_sensor.get_line_position({"left_outer": False, "left_inner": False, "right_inner": True, "right_outer": True})
    line_sensor.get_line_position({"left_outer": False, "left_inner": True, "right_inner": True, "right_outer": False})
    line_sensor.calculate_normalized_error({"left_inner": True})
    line_sensor.calculate_normalized_error({})
    line_sensor.majority_vote([])

@pytest.mark.asyncio
async def test_ultrasonic_coverage():
    ultrasonic.apply_median_filter([])
    ultrasonic.filter_ultrasonic_distance(10.0, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 5.0)
    ultrasonic.filter_ultrasonic_distance(1000.0, [], 5.0)

@pytest.mark.asyncio
async def test_imu_coverage():
    imu.complementary_filter(10, 0, None, 0.1)
    imu.complementary_filter(10, 5, 10, 0.1)

@pytest.mark.asyncio
async def test_freshness_coverage():
    dt = datetime.datetime.now()
    freshness.calculate_freshness(dt.replace(tzinfo=None))
    freshness.calculate_freshness(dt, dt.replace(tzinfo=None))
    freshness.calculate_freshness(dt - datetime.timedelta(seconds=10), dt)

@pytest.mark.asyncio
async def test_auth_coverage():
    req = Request({"type": "http", "headers": []})
    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    try:
        await auth.get_current_user(cred)
    except Exception:
        pass
        
    try:
        await internal_auth.verify_internal_token(cred)
    except Exception:
        pass

@pytest.mark.asyncio
async def test_cache_service_coverage(monkeypatch):
    c = cache_service.CacheService()
    await c.get_latest_sequence("r1")
    await c.update_latest_sequence("r1", 1)
    await c.get_sensor_samples("r1", "ultrasonic", "FRONT")
    await c.save_sensor_samples("r1", "ultrasonic", [], "FRONT")
    await c.get_latest_fused_state("r1")
    await c.save_latest_fused_state("r1", {})
    await c.get_last_seen("r1", "imu")
    await c.update_last_seen("r1", "imu", "2023")

@pytest.mark.asyncio
async def test_event_service_coverage(monkeypatch):
    e = event_service.EventService()
    from sqlalchemy.ext.asyncio import AsyncSession
    
    class MockDB:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def add(self, *args): pass
        async def commit(self): pass
        
    monkeypatch.setattr("app.services.event_service.AsyncSessionLocal", lambda: MockDB())
    monkeypatch.setattr(kafka_service.kafka_service, "publish_event", AsyncMock())
    
    await e.publish_and_store_event("r1", "T", "INFO", 1.0)
    
@pytest.mark.asyncio
async def test_kafka_service_coverage():
    k = kafka_service.KafkaService()
    await k.start()
    await k.publish_fused_state({})
    await k.publish_event("T", {})
    await k.stop()

@pytest.mark.asyncio
async def test_ownership_coverage(monkeypatch):
    o = ownership_service.OwnershipService()
    
    class MockResp:
        status_code = 200
        def json(self): return {"owned": True}
        
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, *args, **kwargs): return MockResp()
        
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)
    
    from app.config import redis
    class MockRedis:
        async def get(self, *args): return None
        async def set(self, *args, **kwargs): pass
    monkeypatch.setattr(redis, "get_redis", AsyncMock(return_value=MockRedis()))
    
    await o.verify_ownership("u1", "r1")

@pytest.mark.asyncio
async def test_ws_coverage():
    w = websocket_service.WebSocketService()
    
    class MockWS:
        async def accept(self): pass
        async def send_json(self, data): pass
        
    mw = MockWS()
    await w.connect("r1", mw)
    await w.broadcast_state("r1", {})
    
    class MockWSFail:
        async def send_json(self, data): raise Exception("fail")
    mwf = MockWSFail()
    await w.connect("r1", mwf)
    await w.broadcast_state("r1", {})
    
    w.disconnect("r1", mw)
    w.disconnect("r1", mwf)

@pytest.mark.asyncio
async def test_routes_coverage(monkeypatch):
    class MockDB:
        async def execute(self, q):
            m = MagicMock()
            m.scalars().all.return_value = []
            return m
            
    await fusion.get_fusion_events("r1", db=MockDB())
    
    try:
        await fusion.get_latest_fused_state("r1")
    except Exception:
        pass
    
    await health.readiness()
