from enum import Enum
from typing import Optional

from pydantic import BaseModel


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
