"""Sell Machine orchestration service (sell-machine-creative-swarm, Change E).

Coordinates the Copywriter (services/copywriter_service.py) and Content Critic
(agents/content_evaluator.py) into a generate -> evaluate -> one-rewrite-pass loop, then hands
surviving hooks to the existing Approval Queue (services/approval_queue_service.py) as a
'campaign_package' draft — calling ApprovalQueueService directly rather than through the
journal-entry-shaped REST endpoint, matching the precedent set by taty_escalation/social_reply
(see design.md Decision 1).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.content_evaluator import evaluate_hook
from services.approval_queue_service import ApprovalQueueService
from services.copywriter_service import generate_hooks, rewrite_hook
from services.crm_service import get_funnel_snapshot
from services.operator_task_service import list_completed_tasks

logger = logging.getLogger(__name__)


def evaluate_hooks(hooks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evaluate a given list of hooks, giving each rejected hook exactly one rewrite attempt,
    and return only the survivors (design.md Decision 7). Backs both `run_creative_loop` and the
    standalone `POST /sell-machine/hooks/evaluate` endpoint."""
    survivors: List[Dict[str, Any]] = []

    for hook in hooks:
        result = evaluate_hook(hook)
        if result["approved"]:
            survivors.append(hook)
            continue

        rewritten = rewrite_hook(hook, reason=result["reason"])
        rewrite_result = evaluate_hook(rewritten)
        if rewrite_result["approved"]:
            survivors.append(rewritten)
        else:
            logger.info(
                "Hook discarded after rewrite still failed evaluation: %s", rewrite_result["reason"]
            )

    return survivors


def _summarize_task_results(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregates a list of completed operator_tasks rows into a small summary: a count plus
    any well-known numeric result fields, tolerant of missing/extra fields (result payload shape
    varies by task_type by design — see hermes-manus-execution-bridge design.md)."""
    summary: Dict[str, Any] = {"count": len(tasks)}
    for field in ("impressions", "clicks", "reach"):
        total = sum((t.get("result") or {}).get(field, 0) or 0 for t in tasks)
        if total:
            summary[field] = total
    return summary


def get_telemetry_report() -> Dict[str, Any]:
    """Aggregates completed post_content/run_ads_ab operator-task results plus the crm_leads
    funnel snapshot (sell-machine-telemetry-loop, Change G). Tolerant of an empty/thin dataset —
    no real Manus results exist until Hermes-side is configured; an empty report is expected,
    not an error."""
    hook_performance = {
        task_type: _summarize_task_results(list_completed_tasks(task_type=task_type))
        for task_type in ("post_content", "run_ads_ab")
    }
    return {
        "hook_performance": hook_performance,
        "funnel_snapshot": get_funnel_snapshot(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_creative_loop(
    count: int = 5, target_segment: Optional[str] = None, use_telemetry: bool = False
) -> List[Dict[str, Any]]:
    """Generate `count` hooks and evaluate them, returning only the survivors.

    `use_telemetry` (sell-machine-telemetry-loop, Change G) opts into fetching the telemetry
    report and passing it to the Copywriter as prior-performance context. Defaults to False, so
    existing callers see no behavior change."""
    report = get_telemetry_report() if use_telemetry else None
    hooks = generate_hooks(count=count, report=report)
    return evaluate_hooks(hooks)


async def create_campaign_package(
    hooks: List[Dict[str, Any]],
    brief: str,
    target_segment: str,
    budget: Optional[int],
) -> Any:
    """Enqueue surviving hooks as a single campaign_package draft in the Approval Queue.

    Returns the created ApprovalDecision. Raises RuntimeError if enqueueing fails.
    """
    draft_id = str(uuid.uuid4())
    package = {
        "hooks": hooks,
        "creative_brief": brief,
        "target_segment": target_segment,
        "budget_cents": budget,
    }

    success, decision, error = await ApprovalQueueService.enqueue_draft(
        draft_id=draft_id,
        draft_type="campaign_package",
        journal_entry=package,
        memo=brief,
    )

    if not success:
        raise RuntimeError(f"Failed to enqueue campaign package: {error}")

    return decision


async def list_campaigns(status: Optional[str] = None) -> List[Any]:
    """List campaign_package drafts from the Approval Queue, optionally filtered by status."""
    return await ApprovalQueueService.list_drafts(draft_type="campaign_package", status=status)
