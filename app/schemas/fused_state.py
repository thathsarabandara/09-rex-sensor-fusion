from datetime import datetime
from typing import Dict

from pydantic import BaseModel


class OrientationState(BaseModel):
    heading_deg: float
    pitch_deg: float
    roll_deg: float
    confidence: float


class MotionState(BaseModel):
    state: str
    confidence: float
    possible_stall: bool


class ObstacleState(BaseModel):
    detected: bool
    direction: str
    distance_cm: float
    risk_level: str
    confidence: float


class LineStateOut(BaseModel):
    detected: bool
    position: str
    normalized_error: float
    confidence: float


class TiltState(BaseModel):
    unsafe: bool
    confidence: float


class ImpactState(BaseModel):
    possible: bool
    confidence: float


class FusedState(BaseModel):
    robot_id: str
    timestamp: datetime
    sequence: int
    orientation: OrientationState
    motion: MotionState
    obstacle: ObstacleState
    line: LineStateOut
    tilt: TiltState
    impact: ImpactState
    sensor_health: Dict[str, str]
    overall_confidence: float
