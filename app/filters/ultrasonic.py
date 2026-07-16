import statistics
from typing import List, Optional, Tuple

from app.config.settings import settings


def get_scan_direction(angle: int) -> str:
    if 0 <= angle <= 60:
        return "RIGHT"
    elif 61 <= angle <= 120:
        return "FRONT"
    elif 121 <= angle <= 180:
        return "LEFT"
    return "UNKNOWN"


def apply_median_filter(samples: List[float]) -> Optional[float]:
    if not samples:
        return None
    return statistics.median(samples)


def apply_ema_filter(
    current_val: float, previous_ema: Optional[float], alpha: float = settings.ULTRASONIC_EMA_ALPHA
) -> float:
    if previous_ema is None:
        return current_val
    return (alpha * current_val) + ((1.0 - alpha) * previous_ema)


def filter_ultrasonic_distance(
    raw_distance: float, recent_samples: List[float], previous_ema: Optional[float]
) -> Tuple[Optional[float], List[float]]:

    if not (
        settings.ULTRASONIC_MIN_DISTANCE_CM <= raw_distance <= settings.ULTRASONIC_MAX_DISTANCE_CM
    ):
        # Invalid value, return None and do not update samples
        return None, recent_samples

    samples = recent_samples + [raw_distance]
    if len(samples) > settings.ULTRASONIC_MEDIAN_WINDOW:
        samples = samples[-settings.ULTRASONIC_MEDIAN_WINDOW :]

    median_val = apply_median_filter(samples)
    if median_val is None:
        return None, samples

    ema_val = apply_ema_filter(median_val, previous_ema)
    return ema_val, samples
