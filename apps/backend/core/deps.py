"""Dependency injection for FastAPI endpoints."""

from fastapi import Header, HTTPException, status
from typing import Optional

from config import settings
from core.security import verify_token
from core.identity_resolver import identity_resolver


# Fallback identity used only when auth is NOT enforced (demo/staging back-compat).
# resolved_user_id/resolved_tenant_id are None here — there's no real JWT to resolve.
_STAGING_USER = {
    "id": "test-user-staging",
    "email": "staging@contexia.test",
    "resolved_user_id": None,
    "resolved_tenant_id": None,
}


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Return the bearer token from an Authorization header, or None."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip() or None
    # Tolerate a raw token without the "Bearer " prefix.
    return authorization.strip() or None


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Resolve the current user from the Authorization header.

    Behavior is gated by ``settings.AUTH_ENFORCED``:
    - When enforced, a valid JWT is required, otherwise ``401``.
    - When not enforced (default for the demo), a missing/invalid token falls back
      to the staging user so existing un-authenticated flows keep working.
    """
    token = _extract_bearer_token(authorization)
    payload = verify_token(token) if token else None

    if payload and payload.get("sub"):
        sub = payload["sub"]
        email = payload.get("email")
        workspace_id = payload.get("tenant_id") or payload.get("workspace_id")
        resolved = identity_resolver.resolve(sub, email, workspace_id)
        return {
            "id": sub,
            "email": email,
            "resolved_user_id": resolved.user_uuid,
            "resolved_tenant_id": resolved.tenant_uuid,
        }

    if settings.AUTH_ENFORCED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Auth not enforced: permissive staging identity for back-compat.
    return dict(_STAGING_USER)


async def verify_resource_ownership(user_id: str, resource_owner_id: str) -> bool:
    """Ensure the authenticated user owns the requested resource.

    Enforced only when ``settings.AUTH_ENFORCED`` is True (raises ``403`` on
    mismatch); otherwise allows access to preserve current demo behavior.
    """
    if settings.AUTH_ENFORCED and str(user_id) != str(resource_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource",
        )
    return True
