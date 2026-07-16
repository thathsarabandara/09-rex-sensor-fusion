from app.config.settings import settings

def is_tilt_unsafe(pitch: float, roll: float) -> bool:
    return abs(pitch) >= settings.UNSAFE_TILT_DEGREES or abs(roll) >= settings.UNSAFE_TILT_DEGREES

def detect_possible_impact(acceleration_x: float, acceleration_y: float, acceleration_z: float) -> bool:
    magnitude = (acceleration_x**2 + acceleration_y**2 + acceleration_z**2)**0.5
    return magnitude >= settings.IMPACT_ACCELERATION_THRESHOLD
