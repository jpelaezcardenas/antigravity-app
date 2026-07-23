"""Dependency injection for FastAPI endpoints."""

import time
from fastapi import Header, HTTPException, status
from typing import Optional

import requests
from jose import JWTError, jwt

from config import settings
from core.security import verify_token
from core.identity_resolver import identity_resolver


# Cache for Supabase's JWKS (public signing keys) — Supabase now signs Auth session
# tokens with an asymmetric key (ES256, rotated rarely) rather than the legacy shared
# HS256 secret. Keys almost never change, so an in-process cache with a generous TTL
# avoids a network round-trip per request; a kid the cache doesn't know about forces
# one refetch (handles key rotation without a restart).
_JWKS_CACHE: dict = {"keys": [], "fetched_at": 0.0}
_JWKS_CACHE_TTL_SECONDS = 3600


def _fetch_supabase_jwks(force: bool = False) -> list:
    """Fetch (and cache) Supabase's public JWKS for verifying asymmetric-signed tokens.
    Never raises — returns whatever is cached (possibly empty) on any failure, so a
    transient network issue degrades to "token not recognized" rather than a 500."""
    now = time.time()
    if not force and _JWKS_CACHE["keys"] and (now - _JWKS_CACHE["fetched_at"]) < _JWKS_CACHE_TTL_SECONDS:
        return _JWKS_CACHE["keys"]
    if not settings.SUPABASE_URL:
        return _JWKS_CACHE["keys"]
    try:
        response = requests.get(
            f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json", timeout=5
        )
        response.raise_for_status()
        keys = response.json().get("keys", [])
        _JWKS_CACHE["keys"] = keys
        _JWKS_CACHE["fetched_at"] = now
        return keys
    except Exception:
        return _JWKS_CACHE["keys"]


def _verify_supabase_token(token: str) -> Optional[dict]:
    """Verifies a Supabase Auth-issued JWT — the same token login.html already stores in
    localStorage["token"] and middleware.ts already validates at the Vercel edge
    (bunker-pwa-auth-enforcement). Returns None (never raises) on any failure, so callers
    fall through cleanly to the existing 401/staging-user behavior.

    Supabase's current default is to sign session tokens asymmetrically (observed: ES256,
    a `kid` in the header, verified via the project's JWKS endpoint) — the legacy shared
    HS256 secret (SUPABASE_JWT_SECRET) cannot verify those at all (wrong algorithm family
    entirely, not just a wrong key). This checks the token's own header to route to the
    right verification path, so it also still accepts a legacy HS256 token/secret."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    alg = header.get("alg")
    kid = header.get("kid")

    if alg and alg != "HS256" and kid:
        keys = _fetch_supabase_jwks()
        matching_key = next((k for k in keys if k.get("kid") == kid), None)
        if matching_key is None:
            # Unknown kid could mean key rotation — refetch once before giving up.
            keys = _fetch_supabase_jwks(force=True)
            matching_key = next((k for k in keys if k.get("kid") == kid), None)
        if matching_key is None:
            return None
        try:
            return jwt.decode(token, matching_key, algorithms=[alg], audience="authenticated")
        except JWTError:
            return None

    if not settings.SUPABASE_JWT_SECRET:
        return None
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError:
        return None


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
    if not payload and token:
        payload = _verify_supabase_token(token)

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
