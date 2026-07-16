from fastapi import APIRouter
from app.schemas.common import ResponseModel
from app.config.database import engine
from app.config.redis import get_redis
import httpx
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

@router.get("/health/live")
async def liveness():
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness():
    status = {"mysql": False, "redis": False, "robot_service": False}
    
    # Check MySQL
    try:
        async with engine.connect() as conn:
            status["mysql"] = True
    except Exception as e:
        logger.error(f"MySQL health check failed: {e}")
        
    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        status["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        
    # Check Robot Service URL format
    if settings.ROBOT_SERVICE_URL.startswith("http"):
        status["robot_service"] = True
        
    overall = all(status.values())
    
    if not overall:
        return {"status": "error", "details": status}
        
    return {"status": "ready", "details": status}
