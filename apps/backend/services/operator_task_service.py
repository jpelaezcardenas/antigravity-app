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
from services.approval_queue_service import ApprovalQueueService

logger = logging.getLogger(__name__)

SIDE_EFFECTING_TASK_TYPES = {"post_content", "run_ads_ab"}
READ_ONLY_TASK_TYPES = {"research", "metrics_pull", "external_integration", "generate_doc"}

Result = Tuple[bool, Optional[Dict[str, Any]], Optional[str]]


def _resolve_cliente_cero_tenant_id(client) -> Optional[str]:
    result = client.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()
    return result.data["id"] if result.data else None


def create_task(task_type: str, payload: Dict[str, Any]) -> Result:
    """Create a read-only operator task directly. Side-effecting task types are rejected —
    they may only be created via `dispatch_campaign_package`, which enforces the approved-draft
    precondition itself."""
    if task_type in SIDE_EFFECTING_TASK_TYPES:
        return False, None, (
            f"task_type '{task_type}' is side-effecting and cannot be created directly; "
            "use the campaign-package dispatch endpoint instead"
        )
    if task_type not in READ_ONLY_TASK_TYPES:
        return False, None, f"unknown task_type '{task_type}'"

    try:
        client = get_service_supabase()
        tenant_id = _resolve_cliente_cero_tenant_id(client)
        row = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "task_type": task_type,
            "payload": payload,
        }
        result = client.table("operator_tasks").insert(row).execute()
        return True, result.data[0], None
    except Exception as e:
        logger.error("operator_task_service.create_task error: %s", str(e))
        return False, None, str(e)


def list_pending_tasks() -> List[Dict[str, Any]]:
    """List all operator_tasks rows with status='pending', oldest first."""
    client = get_service_supabase()
    result = (
        client.table("operator_tasks")
        .select("*")
        .eq("status", "pending")
        .order("created_at")
        .execute()
    )
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
        tenant_id = _resolve_cliente_cero_tenant_id(client)
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
