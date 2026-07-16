import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketService:
    def __init__(self):
        # Maps robot_id -> list of active connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, robot_id: str, websocket: WebSocket):
        await websocket.accept()
        if robot_id not in self.active_connections:
            self.active_connections[robot_id] = []
        self.active_connections[robot_id].append(websocket)
        logger.info(f"WebSocket client connected to robot {robot_id}")

    def disconnect(self, robot_id: str, websocket: WebSocket):
        if robot_id in self.active_connections:
            if websocket in self.active_connections[robot_id]:
                self.active_connections[robot_id].remove(websocket)
            if not self.active_connections[robot_id]:
                del self.active_connections[robot_id]
        logger.info(f"WebSocket client disconnected from robot {robot_id}")

    async def broadcast_state(self, robot_id: str, state_dict: dict):
        if robot_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[robot_id]:
                try:
                    await connection.send_json(state_dict)
                except Exception as e:
                    logger.debug(f"Failed to send websocket message: {e}")
                    dead_connections.append(connection)

            for dead in dead_connections:
                self.disconnect(robot_id, dead)


websocket_service = WebSocketService()
