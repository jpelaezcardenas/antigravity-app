"""
RBAC (Role-Based Access Control) Module
Phase 3B: Customer Onboarding System

Enforces role-based permissions at application level.
Works in conjunction with:
  - RLS policies (database-level tenant isolation)
  - user_roles table (user → role assignment per tenant)
  - role_permissions table (role → permission matrix)
"""

from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

logger = logging.getLogger(__name__)


class RBACError(Exception):
    """Custom exception for RBAC violations."""
    pass


async def get_user_role(
    user_id: str,
    tenant_id: str,
    session: AsyncSession
) -> Optional[str]:
    """
    Get user's role in a specific tenant.

    Args:
        user_id: UUID of the user
        tenant_id: UUID of the tenant
        session: Database session

    Returns:
        Role name (str) or None if user not in tenant
    """
    from main import db

    query = select(db.user_roles.c.role).where(
        and_(
            db.user_roles.c.user_id == user_id,
            db.user_roles.c.tenant_id == tenant_id
        )
    )
    result = await session.execute(query)
    role = result.scalar_one_or_none()
    return role


async def get_tenant_plan(
    tenant_id: str,
    session: AsyncSession
) -> Optional[str]:
    """
    Get tenant's plan (starter, pro, enterprise).

    Args:
        tenant_id: UUID of the tenant
        session: Database session

    Returns:
        Plan name (str) or None if tenant not found
    """
    from main import db

    query = select(db.tenants.c.plan).where(
        db.tenants.c.id == tenant_id
    )
    result = await session.execute(query)
    plan = result.scalar_one_or_none()
    return plan


async def has_permission(
    role: str,
    resource: str,
    action: str,
    session: AsyncSession
) -> bool:
    """
    Check if role has permission for resource+action.

    Args:
        role: Role name (admin, finance, marketing, etc.)
        resource: Resource name (alerts, approval_queue, shadow_gl, etc.)
        action: Action name (read, create, update, delete, admin)
        session: Database session

    Returns:
        True if permission exists, False otherwise
    """
    from main import db

    # Admin bypasses all permission checks
    if role == 'admin':
        return True

    query = select(db.role_permissions.c.id).where(
        and_(
            db.role_permissions.c.role == role,
            db.role_permissions.c.resource == resource,
            db.role_permissions.c.action == action
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def is_role_allowed_for_plan(
    role: str,
    plan: str
) -> bool:
    """
    Check if role is allowed for customer plan.

    Plan restrictions:
    - starter: admin, finance, viewer
    - pro: admin, finance, marketing, growth, operator, viewer
    - enterprise: all roles (+ custom)

    Args:
        role: Role name
        plan: Plan type (starter, pro, enterprise)

    Returns:
        True if role allowed for plan, False otherwise
    """
    allowed_roles = {
        'starter': {'admin', 'finance', 'viewer'},
        'pro': {'admin', 'finance', 'marketing', 'growth', 'operator', 'viewer'},
        'enterprise': {'admin', 'finance', 'marketing', 'growth', 'operator', 'viewer'}
    }

    if plan not in allowed_roles:
        return False

    return role in allowed_roles[plan]


async def check_permission(
    request: Request,
    resource: str,
    action: str,
    session: AsyncSession,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> bool:
    """
    Main permission check function.

    Called by endpoints to verify authorization:

    Usage:
        @router.post("/approve-invoice")
        async def approve_invoice(request: Request, payload: ApproveRequest):
            if not await check_permission(request, "approval_queue", "update", session):
                raise HTTPException(status_code=403, detail="Not authorized")
            # ... continue

    Args:
        request: FastAPI request object
        resource: Resource being accessed
        action: Action being attempted
        session: Database session
        user_id: Optional override user_id (for testing)
        tenant_id: Optional override tenant_id (for testing)

    Returns:
        True if authorized, False otherwise

    Raises:
        HTTPException(403) if user/tenant not found
    """
    # Get IDs from request or parameters
    if user_id is None:
        user_id = getattr(request.state, 'user_id', None)
    if tenant_id is None:
        tenant_id = getattr(request.state, 'tenant_id', None)

    if not user_id or not tenant_id:
        logger.warning(f"Missing user_id or tenant_id in permission check")
        return False

    # Get user's role
    role = await get_user_role(user_id, tenant_id, session)
    if not role:
        logger.warning(f"User {user_id} not in tenant {tenant_id}")
        return False

    # Admin bypasses all checks
    if role == 'admin':
        logger.debug(f"User {user_id} is admin, granting {action} on {resource}")
        return True

    # Check permission in matrix
    has_perm = await has_permission(role, resource, action, session)
    if has_perm:
        logger.debug(f"User {user_id} (role={role}) granted {action} on {resource}")
    else:
        logger.warning(f"User {user_id} (role={role}) denied {action} on {resource}")

    return has_perm


async def enforce_permission(
    request: Request,
    resource: str,
    action: str,
    session: AsyncSession
) -> None:
    """
    Enforce permission check and raise 403 if unauthorized.

    Convenience wrapper around check_permission() that raises HTTPException.

    Usage:
        @router.post("/approve-invoice")
        async def approve_invoice(request: Request, payload: ApproveRequest):
            await enforce_permission(request, "approval_queue", "update", session)
            # ... continue (guaranteed to have permission)

    Args:
        request: FastAPI request object
        resource: Resource being accessed
        action: Action being attempted
        session: Database session

    Raises:
        HTTPException(403) if not authorized
    """
    has_perm = await check_permission(request, resource, action, session)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to {action} {resource}"
        )


async def get_user_permissions(
    user_id: str,
    tenant_id: str,
    session: AsyncSession
) -> List[Dict[str, str]]:
    """
    Get all permissions for a user in a tenant.

    Useful for building permission matrix on frontend.

    Returns:
        List of {"resource": "...", "action": "..."} dicts
    """
    from main import db

    role = await get_user_role(user_id, tenant_id, session)
    if not role:
        return []

    query = select(
        db.role_permissions.c.resource,
        db.role_permissions.c.action
    ).where(db.role_permissions.c.role == role)

    result = await session.execute(query)
    permissions = [
        {"resource": row[0], "action": row[1]}
        for row in result.fetchall()
    ]
    return permissions


# Permission constants for common checks
PERMISSION_ADMIN_PANEL = ("admin_panel", "read")
PERMISSION_ADMIN_MODIFY = ("admin_panel", "update")
PERMISSION_USERS_MANAGE = ("users", "create")
PERMISSION_USERS_LIST = ("users", "read")
PERMISSION_GL_READ = ("shadow_gl", "read")
PERMISSION_GL_WRITE = ("shadow_gl", "create")
PERMISSION_APPROVALS_READ = ("approval_queue", "read")
PERMISSION_APPROVALS_APPROVE = ("approval_queue", "update")
PERMISSION_ALERTS_READ = ("alerts", "read")
PERMISSION_ALERTS_WRITE = ("alerts", "update")
PERMISSION_OPERATORS_MANAGE = ("operators", "update")
PERMISSION_EXPORT = ("auditoria_reports", "export")
