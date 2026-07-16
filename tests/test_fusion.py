from app.fusion import confidence, health, motion, obstacle, orientation


def test_obstacle_risk():
    assert obstacle.estimate_obstacle_risk(150) == "NONE"
    assert obstacle.estimate_obstacle_risk(75) == "LOW"
    assert obstacle.estimate_obstacle_risk(30) == "MEDIUM"
    assert obstacle.estimate_obstacle_risk(15) == "HIGH"
    assert obstacle.estimate_obstacle_risk(5) == "CRITICAL"


def test_motion_state():
    assert motion.get_motion_state("FORWARD", 50, True, True) == "MOVING_FORWARD"
    assert motion.get_motion_state("LEFT", 0, False, False) == "STATIONARY"


def test_possible_stall():
    assert motion.detect_possible_stall(50, True, False)
    assert not motion.detect_possible_stall(50, True, True)


def test_orientation():
    assert orientation.is_tilt_unsafe(45, 0)
    assert orientation.is_tilt_unsafe(0, 45)
    assert not orientation.is_tilt_unsafe(10, 10)


def test_impact():
    assert orientation.detect_possible_impact(20.0, 0.0, 0.0)
    assert not orientation.detect_possible_impact(0.0, 0.0, 9.8)


def test_health():
    assert health.evaluate_sensor_health("UNAVAILABLE", 0, 0).value == "UNAVAILABLE"
    assert health.evaluate_sensor_health("STALE", 0, 0).value == "STALE"
    assert health.evaluate_sensor_health("FRESH", 6, 10).value == "DEGRADED"


def test_confidence():
    assert confidence.calculate_confidence("FRESH", "HEALTHY") == 1.0
    assert confidence.calculate_confidence("AGING", "HEALTHY") == 0.8
    assert confidence.calculate_confidence("FRESH", "FAILED") == 0.0
