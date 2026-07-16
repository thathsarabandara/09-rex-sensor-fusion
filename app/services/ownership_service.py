import logging

import httpx

from app.config.redis import get_redis
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OwnershipService:
    async def verify_ownership(self, user_id: str, robot_id: str) -> bool:
        redis = await get_redis()
        cache_key = f"rex:fusion:ownership:{user_id}:{robot_id}"
        cached = await redis.get(cache_key)
        if cached is not None:
            return cached == "1"

        # Verify via Robot Service
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {settings.INTERNAL_SERVICE_TOKEN}"}
                url = (
                    f"{settings.ROBOT_SERVICE_URL}/internal/v1/robots/"
                    f"{robot_id}/ownership/{user_id}"
                )
                response = await client.get(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    owned = data.get("owned", False)
                    await redis.set(
                        cache_key, "1" if owned else "0", ex=settings.OWNERSHIP_CACHE_TTL_SECONDS
                    )
                    return owned
                else:
                    logger.warning(f"Ownership check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error checking ownership: {e}")
            return False


ownership_service = OwnershipService()
