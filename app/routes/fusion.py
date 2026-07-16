from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.services.cache_service import cache_service
from app.services.ownership_service import ownership_service
from app.schemas.common import ResponseModel, ErrorDetail
from app.schemas.fused_state import FusedState
from app.models.fusion_event import FusionEvent

router = APIRouter(tags=["Fusion API"])

async def verify_robot_access(robot_id: str, user=Depends(get_current_user)):
    user_id = user.get("sub")
    if not await ownership_service.verify_ownership(user_id, robot_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "ROBOT_NOT_OWNED", "message": "User does not own this robot"}}
        )
    return user_id

@router.get("/latest", response_model=ResponseModel[dict])
async def get_latest_fused_state(robot_id: str, _=Depends(verify_robot_access)):
    state = await cache_service.get_latest_fused_state(robot_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "FUSED_STATE_NOT_FOUND", "message": "Fused state is not currently available"}}
        )
    # Filter out internal tracking data
    if "_internal" in state:
        del state["_internal"]
    return ResponseModel(success=True, data=state)

@router.get("/sensor-health", response_model=ResponseModel[dict])
async def get_sensor_health(robot_id: str, _=Depends(verify_robot_access)):
    state = await cache_service.get_latest_fused_state(robot_id)
    if not state:
        return ResponseModel(success=True, data={})
    return ResponseModel(success=True, data=state.get("sensor_health", {}))

@router.get("/obstacle", response_model=ResponseModel[dict])
async def get_obstacle_state(robot_id: str, _=Depends(verify_robot_access)):
    state = await cache_service.get_latest_fused_state(robot_id)
    if not state:
        return ResponseModel(success=True, data={})
    return ResponseModel(success=True, data=state.get("obstacle", {}))

@router.get("/line", response_model=ResponseModel[dict])
async def get_line_state(robot_id: str, _=Depends(verify_robot_access)):
    state = await cache_service.get_latest_fused_state(robot_id)
    if not state:
        return ResponseModel(success=True, data={})
    return ResponseModel(success=True, data=state.get("line", {}))

@router.get("/motion", response_model=ResponseModel[dict])
async def get_motion_state(robot_id: str, _=Depends(verify_robot_access)):
    state = await cache_service.get_latest_fused_state(robot_id)
    if not state:
        return ResponseModel(success=True, data={})
    return ResponseModel(success=True, data=state.get("motion", {}))

@router.get("/orientation", response_model=ResponseModel[dict])
async def get_orientation_state(robot_id: str, _=Depends(verify_robot_access)):
    state = await cache_service.get_latest_fused_state(robot_id)
    if not state:
        return ResponseModel(success=True, data={})
    return ResponseModel(success=True, data=state.get("orientation", {}))

@router.get("/events", response_model=ResponseModel[list])
async def get_fusion_events(
    robot_id: str,
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_robot_access)
):
    query = select(FusionEvent).where(FusionEvent.robot_id == robot_id).order_by(FusionEvent.occurred_at.desc())
    if event_type:
        query = query.where(FusionEvent.event_type == event_type)
        
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    events = result.scalars().all()
    
    event_list = []
    for e in events:
        event_list.append({
            "id": e.id,
            "event_type": e.event_type,
            "severity": e.severity,
            "confidence": e.confidence,
            "data": e.data,
            "occurred_at": e.occurred_at.isoformat()
        })
        
    return ResponseModel(success=True, data=event_list)
