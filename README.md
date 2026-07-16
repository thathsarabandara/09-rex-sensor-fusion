# REX Sensor Fusion Engine

## Overview
The REX Sensor Fusion Engine (`09-rex-sensor-fusion`) converts noisy and incomplete robot sensor readings into a cleaner and more reliable fused state.

### Why Sensor Fusion is Required
Raw sensor data is inherently noisy and subject to intermittent dropouts. Without filtering and fusion, navigation systems would make erratic decisions. This microservice applies mathematical filters (median, EMA, low-pass, complementary) to raw telemetry to provide stable situational awareness.

## Responsibilities
- Validating incoming sensor payloads.
- Tracking sensor freshness and detecting stale sequences.
- Aligning readings within a configurable fusion window.
- Filtering ultrasonic distance and mapping scan angles to directions.
- Filtering IMU (accelerometer/gyro) for orientation, unsafe tilt, and possible impacts.
- Filtering IR line-sensor values using majority voting and debouncing.
- Estimating motion state and possible stalls.
- Estimating sensor health and heuristic confidence scores.
- Exposing fused-state data through REST and WebSockets.
- Publishing state transitions through Kafka.

## Service Boundaries
### Sensor Fusion Engine Owns
- Sensor filtering, freshness, health, alignment, and heuristic confidence.
- Obstacle state, line position, orientation, and motion estimation.
- Latest fused state and important fusion-event history.

### Telemetry Service Owns
- MQTT telemetry ingestion and historical raw data.

### Robot Service Owns
- Robot registration, ownership, authentication, and manual commands.

### Navigation Engine Owns
- Movement decisions, obstacle avoidance, and path planning.

### Event Engine Owns
- Complex event correlation and advanced anomaly detection.

## System Communication Flow
### Sensor Input Flow
`ESP32 Robot -> MQTT -> Telemetry Service -> Normalized Kafka sensor snapshot -> Sensor Fusion Engine`

### Fusion Output Flow
`Sensor Fusion Engine -> Kafka fused-state events -> Navigation Engine, Robot Service, Event Engine, Agent Runtime`

### Dashboard Flow
`Web or Mobile App -> API Gateway -> Sensor Fusion Engine REST or WebSocket`

## Input Kafka Contract
Consumes topic: `rex.telemetry.sensor-snapshot.v1`
Payload format:
```json
{
  "event_id": "event-uuid",
  "event_type": "sensor_snapshot",
  "event_version": 1,
  "occurred_at": "2026-07-15T10:30:00.200Z",
  "robot_id": "robot-uuid",
  "sequence": 8442,
  "sensors": {
    "ultrasonic": {
      "distance_cm": 18.7,
      "scan_angle_deg": 90
    }
  },
  "robot_state": {
    "mode": "MANUAL",
    "commanded_direction": "FORWARD",
    "commanded_speed": 55,
    "motor_active": true
  }
}
```

## Filters and Fusion Logic
- **Ultrasonic Filtering:** Values outside limits are rejected. Applies a median filter (default 5 samples) followed by exponential smoothing (EMA alpha=0.35).
- **IMU Filtering:** Low-pass filter for acceleration (alpha=0.25) and complementary filter for pitch and roll (alpha=0.98).
- **IR Line-Sensor Filtering:** Majority voting over a short window (default 5 samples) to debounce readings.
- **Timestamp Alignment:** Sensor observations outside the configurable fusion window (default 250ms) are considered stale.
- **Sensor Freshness:** Evaluated as FRESH, AGING, STALE, or UNAVAILABLE based on current time vs. last observation.
- **Sensor Health:** Uses freshness, missing samples, and processing errors to assign health (HEALTHY, DEGRADED, STALE, FAILED, UNAVAILABLE).
- **Obstacle Fusion:** Maps ultrasonic distance to risk levels (NONE, LOW, MEDIUM, HIGH, CRITICAL).
- **Line-Position Estimation:** Uses active IR channels to determine position (LEFT, CENTER, RIGHT, LOST, WIDE).
- **Motion-State Estimation:** Uses commanded values and acceleration to estimate state (MOVING_FORWARD, STATIONARY, etc.).
- **Stall Detection:** Flags `possible_stall` if commanded to move but no acceleration/heading change is observed for a set duration.
- **Tilt and Impact Detection:** Pitch/roll beyond threshold sets unsafe tilt; acceleration magnitude spike sets possible impact.
- **Heuristic Confidence Scores:** Calculates a heuristic engineering confidence score (0.0 to 1.0) based on freshness and health.

## Fused-State Payload
```json
{
  "robot_id": "robot-uuid",
  "timestamp": "2026-07-15T10:30:00.250Z",
  "sequence": 8442,
  "orientation": { "heading_deg": 128.4, "pitch_deg": 1.8, "roll_deg": -0.9, "confidence": 0.88 },
  "motion": { "state": "MOVING_FORWARD", "confidence": 0.84, "possible_stall": false },
  "obstacle": { "detected": true, "direction": "FRONT", "distance_cm": 18.6, "risk_level": "HIGH", "confidence": 0.94 },
  "line": { "detected": true, "position": "CENTER", "normalized_error": 0.06, "confidence": 0.91 },
  "tilt": { "unsafe": false, "confidence": 0.93 },
  "impact": { "possible": false, "confidence": 0.87 },
  "sensor_health": { "ultrasonic": "HEALTHY", "imu": "HEALTHY", "line_sensor": "HEALTHY", "vision": "UNAVAILABLE" },
  "overall_confidence": 0.89
}
```

## Kafka Topics
- **Consumed:** `rex.telemetry.sensor-snapshot.v1`
- **Published:** `rex.sensor-fusion.state.updated.v1`, `rex.sensor-fusion.obstacle.detected.v1`, `rex.sensor-fusion.line.lost.v1`, etc.

## REST Routes & WebSockets
Base prefix: `/api/v1`
- `GET /robots/{robot_id}/fusion/latest`
- `GET /robots/{robot_id}/fusion/sensor-health`
- `GET /robots/{robot_id}/fusion/obstacle`
- `GET /robots/{robot_id}/fusion/line`
- `GET /robots/{robot_id}/fusion/motion`
- `GET /robots/{robot_id}/fusion/orientation`
- `GET /robots/{robot_id}/fusion/events`
- `WS /api/v1/ws/robots/{robot_id}/fusion`

## Authentication & Ownership
- Validates user JWTs via `rex-auth-service`.
- Verifies robot ownership via internal endpoint on `rex-robot-service`.
- WebSockets require token verification prior to connection.

## Redis Design & MySQL Models
- **Redis:** Maintains short-term sensor windows, freshness keys, health keys, and latest fused state with short TTLs.
- **MySQL:** Stores `FusionEvent` (for transition events) and `FusedStateSample` (optional sampling).

## Repository Structure
Standard Python FastAPI structure with `/app`, `/tests`, `/migrations`, and GitHub/Jenkins configs.

## Environment Variables
Refer to `.env.example` for all configurable environment variables.

## Local Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Alembic Migrations
Run `alembic upgrade head` to apply all database changes.

## Running Tests
Run the test suite and achieve minimum coverage (90% required):
```bash
ruff check .
mypy app
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

## Docker Build and Run
```bash
docker build -t rex-sensor-fusion .
docker run --env-file .env -p 8000:8000 rex-sensor-fusion
```

## CI/CD (GitHub Actions & Jenkins)
- CI workflows are defined in `.github/workflows/ci.yml` and `Jenkinsfile`.
- Builds Docker image and pushes to `ghcr.io/OWNER/09-rex-sensor-fusion`.

## Security Notes
- JWT and Internal tokens are validated.
- Sensitive info is not logged.
- WebSockets enforce ownership checks.

## Known Limitations
- MPU6050 heading may drift without a magnetometer.
- Motion state is estimated and is not wheel odometry.
- Stall detection is heuristic.
- Confidence scores are not calibrated probabilities.
- Ultrasonic scanning is not SLAM.
- Cloud-side fusion must not replace firmware safety checks.
- Emergency stopping must remain available locally on the robot.
- Wheel encoders would significantly improve motion estimation.

## Future Improvements
- Optional vision input fusion.
- Optional sensor integration (lidar, bumpers).
