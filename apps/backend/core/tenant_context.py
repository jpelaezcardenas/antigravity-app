"""Shared tenant-resolution helper.

Extracted from services/operator_task_service.py (hermes-manus-execution-bridge, Change F) so
other write paths (approval_queue_service, centinela_service) can stamp the real Cliente Cero
tenant_id at write time instead of relying on column defaults — see
hermes-multi-tenant-wrapper/tasks.md, Ground Truth Correction #3.
"""

from __future__ import annotations

from typing import Optional


def resolve_cliente_cero_tenant_id(client) -> Optional[str]:
    """Look up the real Cliente Cero tenant UUID via the `tenants` table.

    Returns None if no row is flagged `is_cliente_cero` (caller decides whether that's fatal).
    """
    result = client.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()
    return result.data["id"] if result.data else None
