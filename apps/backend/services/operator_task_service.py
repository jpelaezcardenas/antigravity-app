"""Operator task service (hermes-manus-execution-bridge, Change F).

Generic operator-task queue bridging approved Sell Machine output (and other operational asks)
to external execution via Hermes/Manus. Hermes (local, on-prem) polls `list_pending_tasks`,
claims work via `mark_dispatched`, and writes results back via `report_result`. Side-effecting
task types (post_content, run_ads_ab) may only be created via `dispatch_campaign_package`, which
reads an already-approved `campaign_package` draft from the existing Approval Queue
(services/approval_queue_service.py, read-only — never modified by this module).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from core.supabase_client import get_service_supabase
from core.tenant_context import resolve_cliente_cero_tenant_id, tenant_exists
from services.approval_queue_service import ApprovalQueueService

logger = logging.getLogger(__name__)

SIDE_EFFECTING_TASK_TYPES = {"post_content", "run_ads_ab"}
READ_ONLY_TASK_TYPES = {"research", "metrics_pull", "external_integration", "generate_doc"}

Result = Tuple[bool, Optional[Dict[str, Any]], Optional[str]]


def _resolve_cliente_cero_tenant_id(client) -> Optional[str]:
    """Thin wrapper kept for backward compatibility with existing test patches
    (`patch("services.operator_task_service._resolve_cliente_cero_tenant_id", ...)`);
    delegates to the shared core.tenant_context helper (Ground Truth Correction #3)."""
    return resolve_cliente_cero_tenant_id(client)


def create_task(
    task_type: str, payload: Dict[str, Any], tenant_id: Optional[str] = None
) -> Result:
    """Create a read-only operator task directly. Side-effecting task types are rejected —
    they may only be created via `dispatch_campaign_package`, which enforces the approved-draft
    precondition itself.

    When `tenant_id` is supplied, it is validated against the `tenants` table and used directly
    (no Cliente Cero involvement). When omitted, falls back to the Cliente Cero tenant and logs
    a warning recording that an explicit tenant was not supplied. If the resolver also returns
    None (no Cliente Cero tenant configured), the task is rejected."""
    if task_type in SIDE_EFFECTING_TASK_TYPES:
        return False, None, (
            f"task_type '{task_type}' is side-effecting and cannot be created directly; "
            "use the campaign-package dispatch endpoint instead"
        )
    if task_type not in READ_ONLY_TASK_TYPES:
        return False, None, f"unknown task_type '{task_type}'"

    try:
        client = get_service_supabase()

        if tenant_id is not None:
            if not tenant_exists(client, tenant_id):
                return False, None, f"tenant {tenant_id} not found"
            resolved_tenant_id = tenant_id
        else:
            resolved_tenant_id = _resolve_cliente_cero_tenant_id(client)
            logger.warning(
                "create_task: no tenant_id supplied; falling back to Cliente Cero tenant %s "
                "(task_type=%s)",
                resolved_tenant_id,
                task_type,
            )
            if resolved_tenant_id is None:
                return False, None, (
                    "no tenant_id supplied and no Cliente Cero tenant configured"
                )

        row = {
            "id": str(uuid.uuid4()),
            "tenant_id": resolved_tenant_id,
            "task_type": task_type,
            "payload": payload,
        }
        result = client.table("operator_tasks").insert(row).execute()
        return True, result.data[0], None
    except Exception as e:
        logger.error("operator_task_service.create_task error: %s", str(e))
        return False, None, str(e)


def list_pending_tasks(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all operator_tasks rows with status='pending', oldest first, optionally filtered by
    tenant_id. Uses an explicit column projection (rather than `select("*")`) so `tenant_id`
    (and the rest of the Hermes-facing contract) can never silently vanish if the table gains
    columns Hermes shouldn't see."""
    client = get_service_supabase()
    query = (
        client.table("operator_tasks")
        .select("id, tenant_id, task_type, payload, status, created_at")
        .eq("status", "pending")
    )
    if tenant_id:
        query = query.eq("tenant_id", tenant_id)
    result = query.order("created_at").execute()
    return result.data


def list_completed_tasks(task_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all operator_tasks rows with status='completed', oldest first, optionally filtered
    by task_type. The read-back capability for Change F's operator-task results, deferred to
    sell-machine-telemetry-loop (Change G)."""
    client = get_service_supabase()
    query = client.table("operator_tasks").select("*").eq("status", "completed")
    if task_type:
        query = query.eq("task_type", task_type)
    result = query.order("created_at").execute()
    return result.data


def mark_dispatched(task_id: str) -> Result:
    """Transition a task from pending -> dispatched. Any other current status is rejected."""
    try:
        client = get_service_supabase()
        existing = (
            client.table("operator_tasks").select("*").eq("id", task_id).single().execute()
        )
        if not existing.data:
            return False, None, f"task {task_id} not found"
        if existing.data["status"] != "pending":
            return False, None, (
                f"task {task_id} is '{existing.data['status']}', not 'pending' — cannot dispatch"
            )

        updated = (
            client.table("operator_tasks")
            .update({"status": "dispatched"})
            .eq("id", task_id)
            .execute()
        )
        return True, updated.data[0], None
    except Exception as e:
        logger.error("operator_task_service.mark_dispatched error: %s", str(e))
        return False, None, str(e)


def report_result(task_id: str, status: str, result: Dict[str, Any]) -> Result:
    """Transition a task from dispatched -> completed|failed, storing the result payload. Only
    accepted from a currently 'dispatched' task."""
    if status not in ("completed", "failed"):
        return False, None, f"invalid terminal status '{status}'"

    try:
        client = get_service_supabase()
        existing = (
            client.table("operator_tasks").select("*").eq("id", task_id).single().execute()
        )
        if not existing.data:
            return False, None, f"task {task_id} not found"
        if existing.data["status"] != "dispatched":
            return False, None, (
                f"task {task_id} is '{existing.data['status']}', not 'dispatched' — "
                "cannot report a result"
            )

        updated = (
            client.table("operator_tasks")
            .update({"status": status, "result": result})
            .eq("id", task_id)
            .execute()
        )
        return True, updated.data[0], None
    except Exception as e:
        logger.error("operator_task_service.report_result error: %s", str(e))
        return False, None, str(e)


async def dispatch_campaign_package(decision_id: str) -> Result:
    """Convert an approved campaign_package Approval Queue draft into a pending post_content
    operator task. Rejects if the decision is not found, not a campaign_package, or not approved.
    Never modifies the Approval Queue row itself."""
    decisions = await ApprovalQueueService.list_drafts(draft_type="campaign_package")
    decision = next((d for d in decisions if d.id == decision_id), None)

    if decision is None:
        return False, None, f"decision {decision_id} not found"

    decision_status = decision.status.value if hasattr(decision.status, "value") else decision.status
    if decision_status != "approved":
        return False, None, (
            f"decision {decision_id} is '{decision_status}', not 'approved' — cannot dispatch"
        )

    try:
        client = get_service_supabase()
        tenant_id = getattr(decision, "tenant_id", None)
        if not tenant_id:
            tenant_id = _resolve_cliente_cero_tenant_id(client)
            logger.warning(
                "dispatch_campaign_package: decision %s has no tenant_id; falling back to "
                "Cliente Cero tenant %s",
                decision_id,
                tenant_id,
            )
        task_type = "run_ads_ab" if decision.payload.get("budget_cents") else "post_content"
        row = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "task_type": task_type,
            "payload": {**decision.payload, "source_decision_id": decision_id},
        }
        result = client.table("operator_tasks").insert(row).execute()
        return True, result.data[0], None
    except Exception as e:
        logger.error("operator_task_service.dispatch_campaign_package error: %s", str(e))
        return False, None, str(e)
