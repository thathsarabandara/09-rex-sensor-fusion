from datetime import datetime, timezone

import pytest

from app.schemas.sensor_snapshot import SensorSnapshot
from app.services.fusion_service import fusion_service


@pytest.mark.asyncio
async def test_process_snapshot(monkeypatch):
    from app.services.cache_service import cache_service
    from app.services.kafka_service import kafka_service
    from app.services.websocket_service import websocket_service

    # Mock everything
    async def mock_get_latest_seq(*args):
        return 0

    async def mock_update_seq(*args):
        pass

    async def mock_get_state(*args):
        return None

    async def mock_update_seen(*args):
        pass

    async def mock_get_samples(*args):
        return []

    async def mock_save_samples(*args):
        pass

    async def mock_save_state(*args):
        pass

    async def mock_get_last_seen(*args):
        return None

    monkeypatch.setattr(cache_service, "get_latest_sequence", mock_get_latest_seq)
    monkeypatch.setattr(cache_service, "update_latest_sequence", mock_update_seq)
    monkeypatch.setattr(cache_service, "get_latest_fused_state", mock_get_state)
    monkeypatch.setattr(cache_service, "update_last_seen", mock_update_seen)
    monkeypatch.setattr(cache_service, "get_sensor_samples", mock_get_samples)
    monkeypatch.setattr(cache_service, "save_sensor_samples", mock_save_samples)
    monkeypatch.setattr(cache_service, "save_latest_fused_state", mock_save_state)
    monkeypatch.setattr(cache_service, "get_last_seen", mock_get_last_seen)

    async def mock_publish(*args):
        pass

    async def mock_broadcast(*args):
        pass

    monkeypatch.setattr(kafka_service, "publish_fused_state", mock_publish)
    monkeypatch.setattr(websocket_service, "broadcast_state", mock_broadcast)

    snapshot = SensorSnapshot(
        event_id="test-id",
        occurred_at=datetime.now(timezone.utc),
        robot_id="r1",
        sequence=1,
        sensors={  # type: ignore
            "ultrasonic": {"distance_cm": 15.0, "scan_angle_deg": 90},
            "imu": {
                "acceleration_x": 0.0,
                "acceleration_y": 0.0,
                "acceleration_z": 9.8,
                "gyro_x": 0.0,
                "gyro_y": 0.0,
                "gyro_z": 0.0,
                "heading_deg": 0.0,
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
            },
            "line": {
                "left_outer": False,
                "left_inner": True,
                "right_inner": True,
                "right_outer": False,
            },
        },
        robot_state={  # type: ignore
            "mode": "MANUAL",
            "commanded_direction": "FORWARD",
            "commanded_speed": 50,
            "motor_active": True,
        },
    )

    # Should run without error
    await fusion_service.process_snapshot(snapshot)
