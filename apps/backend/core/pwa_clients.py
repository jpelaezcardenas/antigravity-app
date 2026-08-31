"""Active PWA client resolver.

Returns the list of B2B clients currently eligible for automated Hermes
agent jobs: those with status='activo' AND provision_status='provisioned'.

The founder controls eligibility by toggling b2b_clients.status via the
Búnker CRM — no separate founder_override field is needed.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActiveClient:
    company_id: str
    tenant_id: str
    nombre: str


def get_active_pwa_clients(supabase_client: Any) -> list[ActiveClient]:
    """Return all B2B clients with active PWA access.

    Uses service-role client so RLS does not filter the result; callers
    MUST apply an explicit tenant_id filter in every downstream query.
    """
    result = (
        supabase_client
        .table("b2b_clients")
        .select("id, tenant_id, name")
        .eq("status", "activo")
        .eq("provision_status", "provisioned")
        .execute()
    )
    return [
        ActiveClient(
            company_id=row["id"],
            tenant_id=row["tenant_id"],
            nombre=row.get("name") or row.get("id"),
        )
        for row in (result.data or [])
    ]
