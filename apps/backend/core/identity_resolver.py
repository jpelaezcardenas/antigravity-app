"""
Identity resolution — bridge JWT string identities to canonical governance UUIDs.

The backend issues its own HS256 JWTs whose `sub` (user) and `workspace_id`
(tenant) may be non-UUID strings: demo users are hardcoded (e.g. `usr_cliente_demo`)
and `create_access_token` defaults `workspace_id` to the literal `"contexia-org-1"`.
The governance tables (`user_tenants`, `user_roles`) key on UUIDs (`usuarios.id`,
`tenants.id`). Without resolution, the membership check cast-errors and fails closed
for every caller (see change agent-operations-multitenant-security, design D7).

This resolver maps the JWT identifiers to canonical UUIDs on the service-role
client, once per connection, before any membership check / cost / audit write.
Fail-closed: any error or unresolved identity yields None (the chokepoint then
blocks the invocation with reason `identity_unresolved`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import logging
import uuid as _uuid

from core.supabase_client import get_service_supabase

logger = logging.getLogger("identity-resolver")


def _is_uuid(value) -> bool:
    """True if `value` is a valid UUID string."""
    if not value:
        return False
    try:
        _uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


@dataclass(frozen=True)
class ResolvedIdentity:
    """Canonical UUIDs for a caller; either may be None if unresolved."""

    user_uuid: Optional[str]
    tenant_uuid: Optional[str]

    @property
    def is_complete(self) -> bool:
        return bool(self.user_uuid) and bool(self.tenant_uuid)


class IdentityResolver:
    """Resolves JWT identities to `usuarios.id` / `tenants.id` via the service client."""

    def __init__(self, client=None) -> None:
        # `client` is injectable for tests; defaults to the lazy service-role client.
        self._client = client

    def _supabase(self):
        return self._client if self._client is not None else get_service_supabase()

    def resolve_user_uuid(self, sub: str, email: Optional[str]) -> Optional[str]:
        """Resolve the caller to `usuarios.id`.

        Prefer `email` (unique, always present in the JWT); fall back to `sub`
        when it is already a UUID. Returns None if neither resolves (fail-closed).
        """
        if email:
            try:
                result = (
                    self._supabase()
                    .table("usuarios")
                    .select("id")
                    .eq("email", email)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    return result.data[0].get("id")
            except Exception as exc:  # fail-closed on any lookup error
                logger.error("User resolution by email failed for %s: %s", email, exc)
                return None

        if _is_uuid(sub):
            return sub
        return None

    def resolve_tenant_uuid(
        self, workspace_id: str, user_uuid: Optional[str]
    ) -> Optional[str]:
        """Resolve the tenant to `tenants.id`.

        Order: UUID passthrough → `tenants.company_id` → the caller's single active
        `user_tenants` membership. Ambiguous (>1) or absent membership → None.
        """
        if _is_uuid(workspace_id):
            return workspace_id

        if workspace_id:
            try:
                result = (
                    self._supabase()
                    .table("tenants")
                    .select("id")
                    .eq("company_id", workspace_id)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    return result.data[0].get("id")
            except Exception as exc:  # fail-closed on any lookup error
                logger.error(
                    "Tenant resolution by company_id failed for %s: %s",
                    workspace_id,
                    exc,
                )
                return None

        if user_uuid:
            try:
                result = (
                    self._supabase()
                    .table("user_tenants")
                    .select("tenant_id")
                    .eq("user_id", user_uuid)
                    .eq("is_active", True)
                    .execute()
                )
                tenant_ids = {
                    row.get("tenant_id")
                    for row in (result.data or [])
                    if row.get("tenant_id")
                }
                if len(tenant_ids) == 1:
                    return next(iter(tenant_ids))
                if len(tenant_ids) > 1:
                    logger.warning(
                        "Ambiguous tenant for user=%s: %d active memberships",
                        user_uuid,
                        len(tenant_ids),
                    )
            except Exception as exc:  # fail-closed on any lookup error
                logger.error(
                    "Tenant resolution by membership failed for user=%s: %s",
                    user_uuid,
                    exc,
                )
                return None

        return None

    def resolve(
        self, sub: str, email: Optional[str], workspace_id: str
    ) -> ResolvedIdentity:
        """Resolve both user and tenant to canonical UUIDs."""
        user_uuid = self.resolve_user_uuid(sub, email)
        tenant_uuid = self.resolve_tenant_uuid(workspace_id, user_uuid)
        return ResolvedIdentity(user_uuid=user_uuid, tenant_uuid=tenant_uuid)


# Shared instance (service-role client)
identity_resolver = IdentityResolver()
