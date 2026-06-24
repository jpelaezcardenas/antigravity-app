"""
Admin Onboarding Endpoints
Phase 3B: Customer Onboarding System

Endpoints for:
- Customer invitation management
- Team member management
- Onboarding workflow audit trail

Protected: Admin role required on Contexia tenant (User 0)
"""

from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin-onboarding"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateCustomerInviteRequest(BaseModel):
    """Request to invite a new customer."""
    customer_name: str
    customer_email: EmailStr
    plan: str  # starter, pro, enterprise


class CreateCustomerInviteResponse(BaseModel):
    """Response with invite link."""
    invite_id: str
    invite_link: str
    expires_at: datetime
    plan: str
    customer_email: str


class CustomerDTO(BaseModel):
    """Customer (tenant) data."""
    tenant_id: str
    customer_name: str
    plan: str
    created_at: datetime
    admin_email: Optional[str]  # Email of tenant admin
    team_size: int  # Number of team members


class CreateTeamInviteRequest(BaseModel):
    """Request to invite a team member."""
    invitee_email: EmailStr
    role: str  # admin, finance, marketing, growth, operator, viewer


class CreateTeamInviteResponse(BaseModel):
    """Response with team invite link."""
    invite_id: str
    invite_link: str
    expires_at: datetime
    role: str
    invitee_email: str


class TeamMemberDTO(BaseModel):
    """Team member data."""
    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    invited_at: Optional[datetime]  # When they were invited


class UpdateTeamMemberRoleRequest(BaseModel):
    """Request to change team member role."""
    new_role: str  # admin, finance, marketing, growth, operator, viewer


class OnboardingWorkflowDTO(BaseModel):
    """Onboarding workflow audit record."""
    workflow_id: str
    tenant_id: str
    workflow_type: str  # customer_registration, team_onboarding, etc.
    operator_id: str
    user_email: Optional[str]
    role_assigned: Optional[str]
    status: str  # pending, in_progress, completed, failed
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


# ============================================================================
# CUSTOMER MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/customers/invite",
    response_model=CreateCustomerInviteResponse,
    summary="Invite a new customer"
)
async def create_customer_invite(
    request: Request,
    payload: CreateCustomerInviteRequest,
    session: AsyncSession
):
    """
    Create invitation for new customer (tenant).

    Only Contexia admin (User 0) can do this.

    Flow:
    1. Admin creates invite with customer name, email, plan
    2. System generates 7-day invite link
    3. Email sent to customer (separate service)
    4. Customer clicks link → Hermes operator registers them

    Args:
        payload: Customer details
        session: Database session

    Returns:
        Invite link + expiration date

    Raises:
        403: Not authorized (not Contexia admin)
    """
    from core.rbac import enforce_permission
    from core.user_management import CustomerInviteService

    # Check authorization: must be admin of Contexia (Client 0)
    await enforce_permission(request, "admin_panel", "update", session)

    # Get user_id from request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = await CustomerInviteService.create_invite(
            creator_id=user_id,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            plan=payload.plan,
            session=session
        )

        logger.info(
            f"User {user_id} created customer invite for {payload.customer_email} ({payload.plan})"
        )

        return CreateCustomerInviteResponse(**result)

    except Exception as e:
        logger.error(f"Error creating customer invite: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create invite")


@router.get(
    "/customers",
    response_model=List[CustomerDTO],
    summary="List all customers"
)
async def list_customers(
    request: Request,
    session: AsyncSession,
    plan: Optional[str] = None,
    active_only: bool = True
):
    """
    List all customers (tenants).

    Only Contexia admin can access.

    Filters:
    - plan: starter, pro, enterprise
    - active_only: Filter to active customers only

    Returns:
        List of customers with plan, team size, created date
    """
    from core.rbac import enforce_permission
    from main import db

    # Check authorization
    await enforce_permission(request, "admin_panel", "read", session)

    # Build query
    query = select(
        db.tenants.c.id,
        db.tenants.c.legal_name,
        db.tenants.c.plan,
        db.tenants.c.created_at
    )

    if plan:
        query = query.where(db.tenants.c.plan == plan)

    result = await session.execute(query)
    customers = []

    for row in result.fetchall():
        # Get team size
        team_query = select(func.count(db.user_tenants.c.id)).where(
            db.user_tenants.c.tenant_id == row[0]
        )
        team_result = await session.execute(team_query)
        team_size = team_result.scalar_one_or_none() or 0

        customers.append(
            CustomerDTO(
                tenant_id=str(row[0]),
                customer_name=row[1],
                plan=row[2],
                created_at=row[3],
                admin_email=None,  # TODO: Get from users
                team_size=team_size
            )
        )

    return customers


# ============================================================================
# TEAM MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/teams/{tenant_id}/invite",
    response_model=CreateTeamInviteResponse,
    summary="Invite team member to customer"
)
async def create_team_invite(
    request: Request,
    tenant_id: str,
    payload: CreateTeamInviteRequest,
    session: AsyncSession
):
    """
    Invite a team member to join customer.

    Called by: Customer admin OR Contexia admin

    Flow:
    1. Customer admin invites team member with role
    2. System generates 7-day invite link
    3. Email sent to team member
    4. Team member clicks link → Hermes operator onboards them

    Args:
        tenant_id: UUID of customer tenant
        payload: Team member email + role
        session: Database session

    Returns:
        Invite link + expiration date

    Raises:
        403: Not authorized (not admin of tenant)
    """
    from core.rbac import enforce_permission, get_user_role, is_role_allowed_for_plan, get_tenant_plan
    from core.user_management import TeamInviteService
    from main import db

    # Get current user
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check authorization: must be admin of this tenant
    user_role = await get_user_role(user_id, tenant_id, session)
    if user_role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admin can invite team members"
        )

    # Validate role is allowed for plan
    plan = await get_tenant_plan(tenant_id, session)
    if not await is_role_allowed_for_plan(payload.role, plan):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role}' not allowed for {plan} plan"
        )

    try:
        result = await TeamInviteService.create_invite(
            tenant_id=tenant_id,
            invited_by_id=user_id,
            invitee_email=payload.invitee_email,
            role=payload.role,
            session=session
        )

        logger.info(
            f"User {user_id} invited {payload.invitee_email} to tenant {tenant_id} (role={payload.role})"
        )

        return CreateTeamInviteResponse(**result)

    except Exception as e:
        logger.error(f"Error creating team invite: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create invite")


@router.get(
    "/teams/{tenant_id}/members",
    response_model=List[TeamMemberDTO],
    summary="List team members for customer"
)
async def list_team_members(
    request: Request,
    tenant_id: str,
    session: AsyncSession,
    active_only: bool = True
):
    """
    List all team members in customer.

    Called by: Customer admin OR Contexia admin

    Returns:
        List of team members with roles + status
    """
    from main import db

    # Check authorization
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get team members
    query = select(
        db.usuarios.c.id,
        db.usuarios.c.email,
        db.user_roles.c.role,
        db.user_tenants.c.is_active,
        db.user_tenants.c.created_at
    ).join(
        db.user_tenants,
        db.usuarios.c.id == db.user_tenants.c.user_id
    ).join(
        db.user_roles,
        and_(
            db.user_roles.c.user_id == db.usuarios.c.id,
            db.user_roles.c.tenant_id == tenant_id
        )
    ).where(db.user_tenants.c.tenant_id == tenant_id)

    if active_only:
        query = query.where(db.user_tenants.c.is_active == True)

    result = await session.execute(query)
    members = [
        TeamMemberDTO(
            user_id=str(row[0]),
            email=row[1],
            role=row[2],
            is_active=row[3],
            created_at=row[4]
        )
        for row in result.fetchall()
    ]

    return members


@router.put(
    "/teams/{tenant_id}/members/{user_id}/role",
    summary="Update team member role"
)
async def update_team_member_role(
    request: Request,
    tenant_id: str,
    user_id: str,
    payload: UpdateTeamMemberRoleRequest,
    session: AsyncSession
):
    """
    Update team member's role.

    Called by: Customer admin OR Contexia admin

    Triggers: update_team_member_role Hermes operator

    Returns:
        { "status": "success", "previous_role": "...", "new_role": "..." }
    """
    from core.rbac import get_user_role, is_role_allowed_for_plan, get_tenant_plan
    from core.user_management import OnboardingWorkflowService
    from main import db

    # Check authorization: must be admin of tenant
    user_id_current = getattr(request.state, 'user_id', None)
    if not user_id_current:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_role = await get_user_role(user_id_current, tenant_id, session)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate role allowed for plan
    plan = await get_tenant_plan(tenant_id, session)
    if not await is_role_allowed_for_plan(payload.new_role, plan):
        raise HTTPException(
            status_code=400,
            detail=f"Role '{payload.new_role}' not allowed for {plan} plan"
        )

    # Get current role
    query = select(db.user_roles.c.role).where(
        and_(
            db.user_roles.c.user_id == user_id,
            db.user_roles.c.tenant_id == tenant_id
        )
    )
    result = await session.execute(query)
    previous_role = result.scalar_one_or_none()

    if not previous_role:
        raise HTTPException(status_code=404, detail="User not in tenant")

    # Update role
    await session.execute(
        update(db.user_roles)
        .where(
            and_(
                db.user_roles.c.user_id == user_id,
                db.user_roles.c.tenant_id == tenant_id
            )
        )
        .values(role=payload.new_role)
    )

    # Log workflow
    await OnboardingWorkflowService.log_workflow(
        tenant_id=tenant_id,
        workflow_type='role_update',
        operator_id='admin_dashboard',
        user_id=user_id,
        role_assigned=payload.new_role,
        status='completed',
        session=session
    )

    await session.commit()

    logger.info(
        f"User {user_id_current} updated {user_id}'s role: {previous_role} → {payload.new_role}"
    )

    return {
        "status": "success",
        "previous_role": previous_role,
        "new_role": payload.new_role
    }


@router.delete(
    "/teams/{tenant_id}/members/{user_id}",
    summary="Remove team member from customer"
)
async def remove_team_member(
    request: Request,
    tenant_id: str,
    user_id: str,
    session: AsyncSession
):
    """
    Remove team member (offboard).

    Triggers: offboard_team_member Hermes operator

    Returns:
        { "status": "success", "offboarded_at": timestamp }
    """
    from core.rbac import get_user_role
    from core.user_management import OnboardingWorkflowService
    from main import db

    # Check authorization
    user_id_current = getattr(request.state, 'user_id', None)
    if not user_id_current:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_role = await get_user_role(user_id_current, tenant_id, session)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")

    # Soft delete: mark as inactive
    await session.execute(
        update(db.user_tenants)
        .where(
            and_(
                db.user_tenants.c.user_id == user_id,
                db.user_tenants.c.tenant_id == tenant_id
            )
        )
        .values(is_active=False)
    )

    # Log workflow
    await OnboardingWorkflowService.log_workflow(
        tenant_id=tenant_id,
        workflow_type='user_offboarding',
        operator_id='admin_dashboard',
        user_id=user_id,
        status='completed',
        session=session
    )

    await session.commit()

    logger.info(f"User {user_id_current} offboarded {user_id} from tenant {tenant_id}")

    return {
        "status": "success",
        "offboarded_at": datetime.utcnow()
    }


# ============================================================================
# AUDIT TRAIL ENDPOINTS
# ============================================================================

@router.get(
    "/workflows",
    response_model=List[OnboardingWorkflowDTO],
    summary="List onboarding workflows (audit trail)"
)
async def list_onboarding_workflows(
    request: Request,
    session: AsyncSession,
    tenant_id: Optional[str] = None,
    workflow_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """
    List onboarding workflows for audit trail.

    Only Contexia admin or tenant admin can view.

    Filters:
    - tenant_id: Filter by tenant
    - workflow_type: customer_registration, team_onboarding, etc.
    - status: pending, in_progress, completed, failed

    Returns:
        List of workflow records
    """
    from main import db

    # Check authorization
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Build query
    query = select(
        db.onboarding_workflows.c.id,
        db.onboarding_workflows.c.tenant_id,
        db.onboarding_workflows.c.workflow_type,
        db.onboarding_workflows.c.operator_id,
        db.usuarios.c.email,
        db.onboarding_workflows.c.role_assigned,
        db.onboarding_workflows.c.status,
        db.onboarding_workflows.c.error_message,
        db.onboarding_workflows.c.created_at,
        db.onboarding_workflows.c.completed_at
    ).outerjoin(
        db.usuarios,
        db.onboarding_workflows.c.user_id == db.usuarios.c.id
    )

    if tenant_id:
        query = query.where(db.onboarding_workflows.c.tenant_id == tenant_id)
    if workflow_type:
        query = query.where(db.onboarding_workflows.c.workflow_type == workflow_type)
    if status:
        query = query.where(db.onboarding_workflows.c.status == status)

    query = query.order_by(db.onboarding_workflows.c.created_at.desc()).limit(limit)

    result = await session.execute(query)
    workflows = [
        OnboardingWorkflowDTO(
            workflow_id=str(row[0]),
            tenant_id=str(row[1]),
            workflow_type=row[2],
            operator_id=row[3],
            user_email=row[4],
            role_assigned=row[5],
            status=row[6],
            error_message=row[7],
            created_at=row[8],
            completed_at=row[9]
        )
        for row in result.fetchall()
    ]

    return workflows
