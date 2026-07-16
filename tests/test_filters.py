from datetime import datetime, timedelta, timezone

from app.filters import freshness, imu, line_sensor, ultrasonic


def test_ultrasonic_direction():
    assert ultrasonic.get_scan_direction(30) == "RIGHT"
    assert ultrasonic.get_scan_direction(90) == "FRONT"
    assert ultrasonic.get_scan_direction(150) == "LEFT"
    assert ultrasonic.get_scan_direction(200) == "UNKNOWN"


def test_ultrasonic_filter():
    val, samples = ultrasonic.filter_ultrasonic_distance(10.0, [11.0, 12.0], None)
    assert val == 11.0
    assert samples == [11.0, 12.0, 10.0]


def test_ultrasonic_invalid():
    val, samples = ultrasonic.filter_ultrasonic_distance(1.0, [11.0], None)
    assert val is None
    assert samples == [11.0]


def test_imu_low_pass():
    res = imu.low_pass_filter(10.0, 5.0, 0.5)
    assert res == 7.5


def test_imu_normalize():
    assert imu.normalize_heading(370) == 10.0
    assert imu.normalize_heading(-10) == 350.0


def test_line_sensor():
    assert line_sensor.majority_vote([True, True, False])
    assert not line_sensor.majority_vote([False, False, True])

    pos = line_sensor.get_line_position(
        {"left_outer": True, "left_inner": True, "right_inner": False, "right_outer": False}
    )
    assert pos == "LEFT"

    err = line_sensor.calculate_normalized_error({"left_inner": True, "right_inner": True})
    assert err == 0.0


def test_freshness():
    now = datetime.now(timezone.utc)
    assert freshness.calculate_freshness(now, now) == "FRESH"
    assert freshness.calculate_freshness(now - timedelta(seconds=2), now) == "AGING"
    assert freshness.calculate_freshness(now - timedelta(seconds=4), now) == "STALE"
