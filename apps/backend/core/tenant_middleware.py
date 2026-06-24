"""
Tenant context middleware for multi-tenant isolation.

Extracts tenant_id from JWT bearer token and injects into FastAPI request context.
Non-invasive: existing endpoints unaware of this middleware.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.security import verify_token
from core.identity_resolver import identity_resolver
import logging

logger = logging.getLogger("tenant-middleware")


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant_id from JWT and injects into request.state.

    Flow:
    1. Extract Authorization: Bearer <JWT> from request headers
    2. Decode JWT and extract tenant_id claim
    3. Inject into request.state.tenant_id (for downstream endpoint access)
    4. Log for observability

    Graceful fallback:
    - If no JWT: sets tenant_id to "default-tenant"
    - If JWT invalid: logs warning, uses default
    - If tenant_id missing from payload: uses default
    """

    async def dispatch(self, request: Request, call_next):
        """Extract tenant context and pass to next middleware/endpoint."""
        tenant_id: str = "default-tenant"
        user_id: str | None = None
        resolved_tenant_id: str | None = None
        resolved_user_id: str | None = None

        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = verify_token(token)

            if payload:
                # Extract tenant_id from JWT payload (claims: sub, tenant_id, email, etc.)
                tenant_id = payload.get("tenant_id", "default-tenant")
                user_id = payload.get("sub")
                email = payload.get("email")

                if not tenant_id or tenant_id == "default-tenant":
                    logger.debug(f"JWT payload missing tenant_id, using default. User: {user_id}")

                # Resolve the JWT's string identities to canonical governance UUIDs
                # (same bridge as the WebSocket path, design D7). Fail-open here:
                # an unresolved identity leaves resolved_* as None without blocking
                # the request — callers that need a UUID check this themselves.
                resolved = identity_resolver.resolve(user_id, email, tenant_id)
                resolved_user_id = resolved.user_uuid
                resolved_tenant_id = resolved.tenant_uuid
            else:
                logger.debug("JWT token invalid or expired, using default tenant")

        # Inject into request context for downstream access
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id
        request.state.resolved_tenant_id = resolved_tenant_id
        request.state.resolved_user_id = resolved_user_id

        # Log for observability (debug level to avoid noise in production)
        logger.debug(
            f"[Tenant: {tenant_id}] {request.method} {request.url.path} | User: {user_id}"
        )

        # Pass to next middleware/endpoint
        response = await call_next(request)

        return response
