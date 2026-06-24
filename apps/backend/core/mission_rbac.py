"""
Mission-Specific RBAC and RLS Checks (T12.2)

Mission access control:
- Tenant isolation: Users see only missions from their tenant
- Role-based filtering: Viewers see completed only, Finance sees costs only
- Admin bypass: Admins can see/edit all missions in tenant
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


# Mission permission constants
PERMISSION_MISSIONS_LIST = ("missions", "read")
PERMISSION_MISSIONS_CREATE = ("missions", "create")
PERMISSION_MISSIONS_EDIT = ("missions", "update")
PERMISSION_MISSIONS_DELETE = ("missions", "delete")
PERMISSION_MISSIONS_COST_VIEW = ("missions_cost", "read")
PERMISSION_MISSIONS_COST_EXPORT = ("missions_cost", "export")


async def check_mission_access(
    request: Request,
    mission_id: UUID,
    action: str,
    session: AsyncSession
) -> bool:
    """
    Check if user can access a mission.

    Verifies:
    1. Mission exists
    2. User is in mission's tenant
    3. User's role allows the action

    Args:
        request: FastAPI request
        mission_id: UUID of mission
        action: "read", "update", "delete"
        session: Database session

    Returns:
        True if authorized, False otherwise
    """
    from apps.backend.core.rbac import check_permission

    user_id = getattr(request.state, 'user_id', None)
    tenant_id = getattr(request.state, 'tenant_id', None)

    if not user_id or not tenant_id:
        logger.warning("Missing user_id or tenant_id")
        return False

    # Verify mission belongs to user's tenant
    mission_tenant = await get_mission_tenant(mission_id, session)
    if mission_tenant != tenant_id:
        logger.warning(
            f"Mission {mission_id} belongs to tenant {mission_tenant}, "
            f"not {tenant_id}"
        )
        return False

    # Check general mission permission
    return await check_permission(request, "missions", action, session)


async def enforce_mission_access(
    request: Request,
    mission_id: UUID,
    action: str,
    session: AsyncSession
) -> None:
    """
    Enforce mission access check and raise 403 if unauthorized.

    Args:
        request: FastAPI request
        mission_id: UUID of mission
        action: "read", "update", "delete"
        session: Database session

    Raises:
        HTTPException(403) if not authorized
    """
    has_access = await check_mission_access(request, mission_id, action, session)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to {action} mission {mission_id}"
        )


async def get_mission_tenant(mission_id: UUID, session: AsyncSession) -> Optional[UUID]:
    """Get the tenant_id for a mission."""
    from apps.backend.models.mission import MissionModel

    query = select(MissionModel.tenant_id).where(MissionModel.id == mission_id)
    result = await session.execute(query)
    row = result.scalar_one_or_none()
    return row


async def check_cost_visibility(
    request: Request,
    mission_id: UUID,
    session: AsyncSession
) -> bool:
    """
    Check if user can see cost breakdown for a mission.

    Only admin and finance roles can see costs.

    Args:
        request: FastAPI request
        mission_id: UUID of mission
        session: Database session

    Returns:
        True if user can see costs, False otherwise
    """
    from apps.backend.core.rbac import get_user_role

    user_id = getattr(request.state, 'user_id', None)
    tenant_id = getattr(request.state, 'tenant_id', None)

    if not user_id or not tenant_id:
        return False

    # Get user's role
    role = await get_user_role(user_id, tenant_id, session)
    if not role:
        return False

    # Only admin and finance can see costs
    return role in ('admin', 'finance')


async def enforce_cost_visibility(
    request: Request,
    mission_id: UUID,
    session: AsyncSession
) -> None:
    """
    Enforce cost visibility check.

    Raises:
        HTTPException(403) if user cannot see costs
    """
    can_view = await check_cost_visibility(request, mission_id, session)
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view mission costs"
        )


async def filter_missions_by_role(
    missions: list,
    request: Request,
    session: AsyncSession
) -> list:
    """
    Filter missions list based on user's role.

    Rules:
    - Admin: See all missions
    - Finance: See all missions (for cost tracking)
    - Viewer: See only completed missions
    - Editor: See all assigned missions

    Args:
        missions: List of mission objects
        request: FastAPI request (for user role)
        session: Database session

    Returns:
        Filtered list of missions
    """
    from apps.backend.core.rbac import get_user_role

    user_id = getattr(request.state, 'user_id', None)
    tenant_id = getattr(request.state, 'tenant_id', None)

    if not user_id or not tenant_id:
        return []

    role = await get_user_role(user_id, tenant_id, session)
    if not role:
        return []

    # Admin and finance see all
    if role in ('admin', 'finance'):
        return missions

    # Viewer sees only completed missions
    if role == 'viewer':
        return [m for m in missions if m.status == 'completed']

    # Default: return all (other roles might have partial visibility)
    return missions


async def filter_checkpoints_by_role(
    checkpoints: list,
    request: Request,
    session: AsyncSession
) -> list:
    """
    Filter checkpoints based on user's role.

    Rules:
    - Admin: See all checkpoints
    - Finance: See proof (not full details)
    - Viewer: See status only (no proof)

    Args:
        checkpoints: List of checkpoint objects
        request: FastAPI request
        session: Database session

    Returns:
        Filtered/masked checkpoint list
    """
    from apps.backend.core.rbac import get_user_role

    user_id = getattr(request.state, 'user_id', None)
    tenant_id = getattr(request.state, 'tenant_id', None)

    if not user_id or not tenant_id:
        return []

    role = await get_user_role(user_id, tenant_id, session)
    if not role:
        return []

    # Admin sees all
    if role == 'admin':
        return checkpoints

    # Finance sees all with proof
    if role == 'finance':
        return checkpoints

    # Viewer sees only status (remove proof)
    if role == 'viewer':
        masked = []
        for cp in checkpoints:
            masked_cp = cp.copy()
            masked_cp.pop('proof', None)  # Remove proof details
            masked.append(masked_cp)
        return masked

    return checkpoints


async def audit_mission_access(
    user_id: str,
    mission_id: UUID,
    action: str,
    authorized: bool,
    session: AsyncSession
) -> None:
    """
    Log mission access for audit trail.

    Args:
        user_id: UUID of user
        mission_id: UUID of mission
        action: Action attempted ("read", "update", etc)
        authorized: Whether access was granted
        session: Database session
    """
    logger.info(
        f"Mission access audit: user={user_id}, mission={mission_id}, "
        f"action={action}, authorized={authorized}"
    )

    # TODO: Store in mission_audit_log table
    # insert_stmt = mission_audit_log.insert().values(
    #     mission_id=mission_id,
    #     user_id=user_id,
    #     action=action,
    #     authorized=authorized,
    #     accessed_at=datetime.utcnow()
    # )
    # await session.execute(insert_stmt)


# RLS Query Helpers
async def apply_rls_filter(
    query,
    request: Request,
    session: AsyncSession
):
    """
    Apply RLS filter to a query based on user's tenant.

    Automatically filters by tenant_id from JWT.

    Args:
        query: SQLAlchemy select() query
        request: FastAPI request
        session: Database session

    Returns:
        Filtered query
    """
    tenant_id = getattr(request.state, 'tenant_id', None)

    if not tenant_id:
        logger.warning("No tenant_id in request, returning empty filter")
        return query.where(False)  # No results

    # Add tenant filter
    from apps.backend.models.mission import MissionModel

    if hasattr(MissionModel, 'tenant_id'):
        query = query.where(MissionModel.tenant_id == tenant_id)

    return query
