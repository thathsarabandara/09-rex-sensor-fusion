import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_monitor_task: Optional[asyncio.Task] = None


async def monitor_loop():
    try:
        while True:
            # We can periodically scan cache for stale sensors and emit events if needed.
            # For simplicity, we assume process_snapshot handles the transitions or we do it here.
            # In a full production system, we'd scan Redis keys like rex:fusion:freshness:*
            await asyncio.sleep(5.0)
    except asyncio.CancelledError:
        logger.info("Stale sensor monitor cancelled")
    except Exception as e:
        logger.error(f"Monitor error: {e}")


def start_monitor():
    global _monitor_task
    _monitor_task = asyncio.create_task(monitor_loop())


async def stop_monitor():
    if _monitor_task:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
