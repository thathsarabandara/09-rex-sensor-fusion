from typing import Dict
from app.schemas.sensor_health import HealthState

def evaluate_sensor_health(freshness: str, invalid_samples: int, total_samples: int) -> HealthState:
    if freshness == "UNAVAILABLE":
        return HealthState.UNAVAILABLE
    if freshness == "STALE":
        return HealthState.STALE
    
    if total_samples > 0:
        invalid_ratio = invalid_samples / total_samples
        if invalid_ratio > 0.5:
            return HealthState.DEGRADED
            
    if freshness == "AGING":
        return HealthState.DEGRADED
        
    return HealthState.HEALTHY
