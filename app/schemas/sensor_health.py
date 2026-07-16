from pydantic import BaseModel
from typing import Optional
from enum import Enum

class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"

class SensorHealth(BaseModel):
    sensor: str
    status: HealthState
    reason: Optional[str] = None
