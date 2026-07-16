import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.config.logging import setup_logging
from app.config.settings import settings
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.routes import fusion, health, websockets
from app.services.kafka_service import kafka_service
from app.workers.sensor_snapshot_consumer import start_consumer, stop_consumer
from app.workers.stale_sensor_monitor import start_monitor, stop_monitor

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")

    # Start background workers
    await kafka_service.start()
    await start_consumer()
    start_monitor()

    yield

    logger.info("Shutting down...")
    await kafka_service.stop()
    await stop_consumer()
    await stop_monitor()


app = FastAPI(
    title="REX Sensor Fusion Engine",
    description="Microservice for robot sensor filtering, fusion and state estimation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(fusion.router, prefix="/api/v1/robots/{robot_id}/fusion")
app.include_router(websockets.router, prefix="/api/v1/ws/robots/{robot_id}/fusion")
app.include_router(health.router)
