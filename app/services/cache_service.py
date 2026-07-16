import json

from app.config.redis import get_redis


class CacheService:
    async def get_latest_sequence(self, robot_id: str) -> int:
        redis = await get_redis()
        key = f"rex:fusion:sequence:{robot_id}"
        val = await redis.get(key)
        return int(val) if val else -1

    async def update_latest_sequence(self, robot_id: str, sequence: int):
        redis = await get_redis()
        key = f"rex:fusion:sequence:{robot_id}"
        await redis.set(key, sequence, ex=86400)  # Keep for 1 day

    async def get_sensor_samples(
        self, robot_id: str, sensor_type: str, direction: str = None
    ) -> list:
        redis = await get_redis()
        key = f"rex:fusion:samples:{robot_id}:{sensor_type}"
        if direction:
            key += f":{direction}"
        data = await redis.get(key)
        return json.loads(data) if data else []

    async def save_sensor_samples(
        self, robot_id: str, sensor_type: str, samples: list, direction: str = None
    ):
        redis = await get_redis()
        key = f"rex:fusion:samples:{robot_id}:{sensor_type}"
        if direction:
            key += f":{direction}"
        await redis.set(key, json.dumps(samples), ex=30)

    async def get_latest_fused_state(self, robot_id: str) -> dict:
        redis = await get_redis()
        key = f"rex:fusion:latest:{robot_id}"
        data = await redis.get(key)
        return json.loads(data) if data else None

    async def save_latest_fused_state(self, robot_id: str, state: dict):
        redis = await get_redis()
        key = f"rex:fusion:latest:{robot_id}"
        await redis.set(key, json.dumps(state), ex=60)

    async def get_last_seen(self, robot_id: str, sensor_type: str) -> str:
        redis = await get_redis()
        key = f"rex:fusion:freshness:{robot_id}"
        data = await redis.hget(key, sensor_type)
        return data

    async def update_last_seen(self, robot_id: str, sensor_type: str, timestamp_iso: str):
        redis = await get_redis()
        key = f"rex:fusion:freshness:{robot_id}"
        await redis.hset(key, sensor_type, timestamp_iso)
        await redis.expire(key, 30)


cache_service = CacheService()
