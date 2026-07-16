from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UltrasonicData(BaseModel):
    distance_cm: float = Field(..., ge=0)
    scan_angle_deg: int = Field(..., ge=0, le=180)


class ImuData(BaseModel):
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    heading_deg: float = Field(..., ge=0, le=360)
    pitch_deg: float
    roll_deg: float


class LineData(BaseModel):
    left_outer: bool
    left_inner: bool
    right_inner: bool
    right_outer: bool


class SensorsData(BaseModel):
    ultrasonic: Optional[UltrasonicData] = None
    imu: Optional[ImuData] = None
    line: Optional[LineData] = None


class RobotStateData(BaseModel):
    mode: str
    commanded_direction: str
    commanded_speed: int = Field(..., ge=0, le=100)
    motor_active: bool = False


class SensorSnapshot(BaseModel):
    event_id: str
    event_type: str = "sensor_snapshot"
    event_version: int = 1
    occurred_at: datetime
    robot_id: str
    sequence: int = Field(..., ge=0)
    sensors: Optional[SensorsData] = None
    robot_state: Optional[RobotStateData] = None
