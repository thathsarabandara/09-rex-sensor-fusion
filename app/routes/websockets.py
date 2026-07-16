from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import jwt
from app.config.settings import settings
from app.services.websocket_service import websocket_service
from app.services.cache_service import cache_service
from app.services.ownership_service import ownership_service
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])

def verify_ws_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token,
            settings.USER_JWT_SECRET_KEY,
            algorithms=[settings.USER_JWT_ALGORITHM],
            issuer=settings.USER_JWT_ISSUER,
            audience=settings.USER_JWT_AUDIENCE
        )
        return payload.get("sub")
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        return None

@router.websocket("")
async def fusion_websocket(websocket: WebSocket, robot_id: str, token: str = None):
    # Depending on how the client sends token. 
    # Usually in query param `?token=...` for websockets.
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
        
    user_id = verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4003, reason="Invalid token")
        return
        
    owned = await ownership_service.verify_ownership(user_id, robot_id)
    if not owned:
        await websocket.close(code=4003, reason="Robot not owned")
        return
        
    await websocket_service.connect(robot_id, websocket)
    
    # Send latest state immediately
    latest_state = await cache_service.get_latest_fused_state(robot_id)
    if latest_state:
        if "_internal" in latest_state:
            del latest_state["_internal"]
        await websocket.send_json(latest_state)
        
    try:
        while True:
            # Keep alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_service.disconnect(robot_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_service.disconnect(robot_id, websocket)
