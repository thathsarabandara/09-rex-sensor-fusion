from typing import Optional

from app.config.settings import settings


def low_pass_filter(
    current: float, previous: Optional[float], alpha: float = settings.IMU_LOW_PASS_ALPHA
) -> float:
    if previous is None:
        return current
    return alpha * current + (1.0 - alpha) * previous


def complementary_filter(
    accel_angle: float,
    gyro_rate: float,
    previous_angle: Optional[float],
    dt: float,
    alpha: float = settings.IMU_COMPLEMENTARY_ALPHA,
) -> float:
    if previous_angle is None:
        return accel_angle
    return alpha * (previous_angle + gyro_rate * dt) + (1.0 - alpha) * accel_angle


def normalize_heading(heading: float) -> float:
    return heading % 360.0
