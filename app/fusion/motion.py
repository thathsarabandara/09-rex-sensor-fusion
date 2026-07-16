from app.config.settings import settings


def get_motion_state(
    commanded_direction: str, commanded_speed: int, motor_active: bool, is_moving_accel: bool
) -> str:
    if not motor_active and commanded_speed == 0:
        return "STATIONARY"

    if motor_active and is_moving_accel:
        if commanded_direction == "FORWARD":
            return "MOVING_FORWARD"
        elif commanded_direction == "BACKWARD":
            return "MOVING_BACKWARD"
        elif commanded_direction == "LEFT":
            return "TURNING_LEFT"
        elif commanded_direction == "RIGHT":
            return "TURNING_RIGHT"

    return "UNKNOWN"


def detect_possible_stall(commanded_speed: int, motor_active: bool, is_moving_accel: bool) -> bool:
    if commanded_speed >= settings.STALL_MIN_SPEED and motor_active and not is_moving_accel:
        return True
    return False
