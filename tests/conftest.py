import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_redis():
    with patch("app.config.redis.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.hset = AsyncMock()
        mock.hget = AsyncMock(return_value=None)
        mock.expire = AsyncMock()
        yield mock
