from datetime import datetime, timezone
from typing import Optional

from app.config.settings import settings


def calculate_freshness(last_seen: datetime, current_time: Optional[datetime] = None) -> str:
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    # Ensure current_time is offset-aware
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    # Ensure last_seen is offset-aware
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    diff_seconds = (current_time - last_seen).total_seconds()

    if diff_seconds < settings.SENSOR_FRESH_SECONDS:
        return "FRESH"
    elif diff_seconds < settings.SENSOR_AGING_SECONDS:
        return "AGING"
    elif diff_seconds < settings.SENSOR_STALE_SECONDS:
        return "STALE"
    else:
        return "UNAVAILABLE"
