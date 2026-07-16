from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "rex-sensor-fusion"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "rex_sensor_fusion"
    MYSQL_USER: str = "rex_user"
    MYSQL_PASSWORD: str = "change-me"

    REDIS_URL: str = "redis://localhost:6379/5"

    USER_JWT_SECRET_KEY: str = "change-me"
    USER_JWT_ALGORITHM: str = "HS256"
    USER_JWT_ISSUER: str = "rex-auth-service"
    USER_JWT_AUDIENCE: str = "rex-platform"

    INTERNAL_SERVICE_TOKEN: str = "change-me"
    ROBOT_SERVICE_URL: str = "http://rex-robot-service:8000"
    OWNERSHIP_CACHE_TTL_SECONDS: int = 60

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CLIENT_ID: str = "rex-sensor-fusion"
    KAFKA_CONSUMER_GROUP: str = "rex-sensor-fusion-v1"
    KAFKA_INPUT_TOPIC: str = "rex.telemetry.sensor-snapshot.v1"
    KAFKA_FUSED_STATE_TOPIC: str = "rex.sensor-fusion.state.updated.v1"

    FUSION_WINDOW_MS: int = 250
    FUSION_OUTPUT_RATE_HZ: int = 5

    ULTRASONIC_MIN_DISTANCE_CM: float = 2.0
    ULTRASONIC_MAX_DISTANCE_CM: float = 400.0
    ULTRASONIC_MEDIAN_WINDOW: int = 5
    ULTRASONIC_EMA_ALPHA: float = 0.35

    OBSTACLE_LOW_DISTANCE_CM: float = 100.0
    OBSTACLE_MEDIUM_DISTANCE_CM: float = 50.0
    OBSTACLE_HIGH_DISTANCE_CM: float = 25.0
    OBSTACLE_CRITICAL_DISTANCE_CM: float = 10.0

    IMU_LOW_PASS_ALPHA: float = 0.25
    IMU_COMPLEMENTARY_ALPHA: float = 0.98
    UNSAFE_TILT_DEGREES: float = 30.0
    IMPACT_ACCELERATION_THRESHOLD: float = 18.0

    LINE_FILTER_WINDOW: int = 5
    LINE_DEBOUNCE_MS: int = 50

    STALL_MIN_SPEED: int = 20
    STALL_DETECTION_SECONDS: float = 2.0

    SENSOR_FRESH_SECONDS: float = 1.0
    SENSOR_AGING_SECONDS: float = 3.0
    SENSOR_STALE_SECONDS: float = 5.0

    PERSIST_FUSED_SAMPLES: bool = True
    FUSED_SAMPLE_INTERVAL_SECONDS: float = 5.0
    FUSION_EVENT_RETENTION_DAYS: int = 90
    FUSED_SAMPLE_RETENTION_DAYS: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
