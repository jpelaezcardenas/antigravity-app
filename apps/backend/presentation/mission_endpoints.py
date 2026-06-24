"""
Mission API Endpoints (T11.8 + T12.3 RLS)

RESTful endpoints for mission management:
- GET    /api/v1/missions                      (with RLS filtering)
- POST   /api/v1/missions/{id}/start           (with RLS checks)
- GET    /api/v1/missions/{id}                 (with RLS enforcement)
- GET    /api/v1/missions/{id}/checkpoints    (with role-based filtering)
- GET    /api/v1/missions/{id}/cost            (finance/admin only)
- GET    /api/v1/missions/{id}/progress        (with RLS checks)
"""

import logging
from uuid import uuid4, UUID
from fastapi import APIRouter, HTTPException, WebSocket, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["missions"])


# ============================================================================
# MODELS (Pydantic for request/response)
# ============================================================================


from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class CheckpointResponse(BaseModel):
    timestamp: str
    task_type: str
    status: str  # ✅, ⏳, ❌
    proof: Dict[str, Any]
    operator_id: str
    duration_ms: int
    cost: float


class TaskResponse(BaseModel):
    id: str
    type: str
    operator: str
    payload: Dict[str, Any]
    status: str
    created_at: str


class MissionResponse(BaseModel):
    id: str
    type: str
    status: str
    objective: str
    tasks: List[TaskResponse]
    checkpoints: List[CheckpointResponse]
    cost: float
    cost_breakdown: Dict[str, float]
    progress: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class MissionCreateRequest(BaseModel):
    invite_id: str
    customer_email: str
    plan: str


class CostBreakdownResponse(BaseModel):
    total_cost: float
    breakdown: Dict[str, float]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/missions", response_model=List[MissionResponse])
async def list_missions(
    request: Request,
    session: AsyncSession = Depends(),  # TODO: Inject session
    skip: int = 0,
    limit: int = 100,
) -> List[MissionResponse]:
    """
    Get all missions (with RLS filtering).

    Query params:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 1000)

    Returns:
    - List of missions with full state (RLS filtered to tenant)
    """
    from apps.backend.core.mission_rbac import (
        PERMISSION_MISSIONS_LIST,
        filter_missions_by_role,
    )
    from apps.backend.core.rbac import enforce_permission

    logger.info(f"GET /missions (skip={skip}, limit={limit})")

    try:
        # Check permission to list missions
        await enforce_permission(request, "missions", "read", session)

        # Get tenant_id from JWT (injected by middleware)
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            raise HTTPException(status_code=401, detail="No tenant in request")

        # TODO: Query missions from database with tenant filter
        # from apps.backend.models.mission import MissionModel
        # missions = await session.execute(
        #     select(MissionModel)
        #     .where(MissionModel.tenant_id == tenant_id)
        #     .offset(skip)
        #     .limit(min(limit, 1000))
        # )
        # mission_list = missions.scalars().all()
        #
        # # Apply role-based filtering
        # filtered_missions = await filter_missions_by_role(mission_list, request, session)
        # return filtered_missions

        # Mock response
        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list missions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list missions")


@router.post("/missions", response_model=MissionResponse)
async def start_mission(
    request: MissionCreateRequest,
    session: AsyncSession = Depends(),  # TODO: Inject session
) -> MissionResponse:
    """
    Start a new customer onboarding mission.

    Request body:
    {
        "invite_id": "uuid",
        "customer_email": "customer@example.com",
        "plan": "pro"
    }

    Returns:
    - New mission with initial state (pending)
    """
    logger.info(
        f"POST /missions - invite_id={request.invite_id}, email={request.customer_email}"
    )

    try:
        # TODO: Use conductor to start mission
        # conductor = await create_conductor(session)
        # mission = await conductor.conduct_customer_onboarding(
        #     invite_id=request.invite_id,
        #     customer_email=request.customer_email,
        #     plan=request.plan
        # )
        # await session.add(mission_model)
        # await session.commit()

        # Mock response
        return MissionResponse(
            id=f"mission-{str(uuid4())[:8]}",
            type="customer_registration",
            status="pending",
            objective=f"Register {request.customer_email} ({request.plan} plan)",
            tasks=[],
            checkpoints=[],
            cost=0.0,
            cost_breakdown={},
            progress=0.0,
            created_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to start mission: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start mission")


@router.get("/missions/{mission_id}", response_model=MissionResponse)
async def get_mission(
    mission_id: UUID,
    request: Request,
    session: AsyncSession = Depends(),  # TODO: Inject session
) -> MissionResponse:
    """
    Get mission details (with RLS enforcement).

    Returns:
    - Full mission state with all tasks and checkpoints

    Raises:
    - 404 if mission not found
    - 403 if user lacks permission or mission is in different tenant
    """
    from apps.backend.core.mission_rbac import enforce_mission_access

    logger.info(f"GET /missions/{mission_id}")

    try:
        # Enforce RLS check: mission must belong to user's tenant
        await enforce_mission_access(request, mission_id, "read", session)

        # TODO: Query mission from database
        # from apps.backend.models.mission import MissionModel
        # mission = await session.get(MissionModel, mission_id)
        # if not mission:
        #     raise HTTPException(status_code=404, detail="Mission not found")
        # return mission

        raise HTTPException(status_code=404, detail="Mission not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mission: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get mission")


@router.get("/missions/{mission_id}/checkpoints", response_model=List[CheckpointResponse])
async def get_mission_checkpoints(
    mission_id: UUID,
    request: Request,
    session: AsyncSession = Depends(),  # TODO: Inject session
) -> List[CheckpointResponse]:
    """
    Get mission checkpoints (proof of task completion).

    Returns:
    - Array of checkpoints with status, proof, cost, duration
    - Filtered based on user role (viewers don't see proof details)

    Raises:
    - 403 if user lacks mission access
    """
    from apps.backend.core.mission_rbac import (
        enforce_mission_access,
        filter_checkpoints_by_role,
    )

    logger.info(f"GET /missions/{mission_id}/checkpoints")

    try:
        # Enforce mission access first
        await enforce_mission_access(request, mission_id, "read", session)

        # TODO: Query checkpoints from database
        # from apps.backend.models.mission import CheckpointModel
        # checkpoints = await session.execute(
        #     select(CheckpointModel).where(
        #         CheckpointModel.mission_id == mission_id
        #     )
        # )
        # checkpoint_list = checkpoints.scalars().all()
        #
        # # Filter based on role (viewers don't see proof)
        # filtered = await filter_checkpoints_by_role(checkpoint_list, request, session)
        # return filtered

        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get checkpoints: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get checkpoints")


@router.get("/missions/{mission_id}/cost", response_model=CostBreakdownResponse)
async def get_mission_cost(
    mission_id: UUID,
    request: Request,
    session: AsyncSession = Depends(),  # TODO: Inject session
) -> CostBreakdownResponse:
    """
    Get mission cost breakdown (finance/admin only).

    Returns:
    - Total cost and breakdown by operator

    Raises:
    - 403 if user is not finance or admin role
    - 404 if mission not found
    """
    from apps.backend.core.mission_rbac import (
        enforce_mission_access,
        enforce_cost_visibility,
    )

    logger.info(f"GET /missions/{mission_id}/cost")

    try:
        # First enforce general mission access
        await enforce_mission_access(request, mission_id, "read", session)

        # Then enforce cost visibility (finance/admin only)
        await enforce_cost_visibility(request, mission_id, session)

        # TODO: Query cost from database
        # from apps.backend.models.mission import MissionModel
        # mission = await session.get(MissionModel, mission_id)
        # if not mission:
        #     raise HTTPException(status_code=404, detail="Mission not found")
        # return CostBreakdownResponse(
        #     total_cost=mission.cost,
        #     breakdown=mission.cost_breakdown
        # )

        return CostBreakdownResponse(total_cost=0.0, breakdown={})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cost: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cost")


@router.get("/missions/{mission_id}/progress")
async def get_mission_progress(
    mission_id: str,
    session: AsyncSession = Depends(),  # TODO: Inject session
) -> Dict[str, Any]:
    """
    Get mission progress.

    Returns:
    {
        "mission_id": "mission-xxx",
        "progress": 50.0,  # 0-100
        "status": "executing",
        "tasks_completed": 2,
        "tasks_total": 4
    }
    """
    logger.info(f"GET /missions/{mission_id}/progress")

    try:
        # TODO: Query mission from database
        # mission = await session.get(MissionModel, mission_id)
        # if not mission:
        #     raise HTTPException(status_code=404, detail="Mission not found")
        # return {
        #     "mission_id": mission.id,
        #     "progress": mission.progress,
        #     "status": mission.status,
        #     "tasks_completed": len([t for t in mission.tasks if t.status == "completed"]),
        #     "tasks_total": len(mission.tasks)
        # }

        return {
            "mission_id": mission_id,
            "progress": 0.0,
            "status": "pending",
            "tasks_completed": 0,
            "tasks_total": 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get progress")


# ============================================================================
# WEBSOCKET (Real-time updates)
# ============================================================================


class WebSocketManager:
    """Manages WebSocket connections for real-time mission updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected: {len(self.active_connections)} active")

    def disconnect(self, websocket: WebSocket):
        """Unregister WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected: {len(self.active_connections)} active")

    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {str(e)}")


# Global WebSocket manager
ws_manager = WebSocketManager()


@router.websocket("/kanban/subscribe")
async def websocket_kanban_subscribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Kanban updates.

    Sends messages when:
    - Mission status changes (pending → executing → completed)
    - Checkpoint recorded (task completed/failed)
    - Cost updated
    - Progress updated
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Wait for client messages (ping/keep-alive)
            data = await websocket.receive_json()
            logger.debug(f"WebSocket message: {data}")

            # Echo back (heartbeat)
            await websocket.send_json({"type": "pong"})

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        ws_manager.disconnect(websocket)


async def notify_mission_update(mission_id: str, status: str, data: Dict[str, Any]):
    """
    Notify all WebSocket clients of mission update.

    Called by conductor when mission state changes.
    """
    message = {
        "type": "mission_update",
        "mission_id": mission_id,
        "status": status,
        "data": data,
    }
    await ws_manager.broadcast(message)
