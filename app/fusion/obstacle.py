from app.config.settings import settings


def estimate_obstacle_risk(distance: float) -> str:
    if distance > settings.OBSTACLE_LOW_DISTANCE_CM:
        return "NONE"
    elif distance > settings.OBSTACLE_MEDIUM_DISTANCE_CM:
        return "LOW"
    elif distance > settings.OBSTACLE_HIGH_DISTANCE_CM:
        return "MEDIUM"
    elif distance > settings.OBSTACLE_CRITICAL_DISTANCE_CM:
        return "HIGH"
    return "CRITICAL"
