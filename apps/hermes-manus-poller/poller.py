"""One tick of the Hermes->Manus loop.

A tick is one-shot and idempotent-by-construction (design.md D1): Task Scheduler fires it every
minute, it does its work, and exits. Nothing is held in memory between ticks — all state lives in
`operator_tasks` (backend) plus the local sidecar (state.py).

Two phases per tick, in this order:
  1. RESOLVE  — for tasks already dispatched from this node, poll Manus and report terminal results.
  2. DISPATCH — claim up to MAX_TASKS_PER_TICK pending tasks and create Manus tasks for them.

Resolve runs first so a backlog drains (finished work is reported) before more is started.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import backend_client
import manus_client
import state
from config import settings
from prompts import build_manus_prompt, build_manus_title

logger = logging.getLogger(__name__)

_REQUIRED_HOOK_KEYS = {"headline", "body", "cta"}
_FENCED_JSON_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _well_shaped_hooks(value: Any) -> Optional[List[Dict[str, Any]]]:
    """Returns `value["hooks"]` if it's a non-empty list of dicts with the required keys, else
    None. Shared by both the structured-output and fenced-JSON extraction tiers so "well-shaped"
    means exactly one thing in this module."""
    hooks = (value or {}).get("hooks") if isinstance(value, dict) else None
    if isinstance(hooks, list) and hooks and all(
        isinstance(h, dict) and _REQUIRED_HOOK_KEYS <= set(h.keys()) for h in hooks
    ):
        return hooks
    return None


def _hooks_from_fenced_json(text: str) -> Optional[List[Dict[str, Any]]]:
    """Manus frequently writes valid JSON inside a fenced ```json code block within free-text
    assistant_message, rather than via the API's native structured_output_result (confirmed live,
    2026-08-15, operator_task 17ee4d8b…). Tries the LAST fenced block in the text (mirrors "last
    successful structured_output_result wins"); returns None on no block, invalid JSON, or a
    parsed object with no well-shaped hooks — never raises."""
    matches = _FENCED_JSON_PATTERN.findall(text)
    if not matches:
        return None
    try:
        parsed = json.loads(matches[-1])
    except (ValueError, TypeError):
        return None
    return _well_shaped_hooks(parsed)


def _extract_manus_output(task_id: str) -> Dict[str, Any]:
    """Retrieves a terminal task's actual output via list_messages (manus-content-retrieval) and
    extracts it into the shape the backend result payload expects. Returns {} if list_messages
    fails or no usable content is found — the caller merges this into the base result dict, so an
    empty extraction never removes the existing status metadata fields.

    Three tiers, most-trusted first: (1) a successful structured_output_result — the API's native
    mechanism; (2) a fenced ```json block inside free-text assistant_message — Manus's common
    fallback behavior when it doesn't use (1); (3) plain assistant_message text, surfaced for human
    review under manus_message, never promoted to a hooks contract it can't back up."""
    messages = manus_client.list_messages(task_id)
    if not messages:
        return {}

    last_structured_hooks = None
    for message in messages:
        structured = message.get("structured_output_result")
        if not structured or not structured.get("success"):
            continue
        hooks = _well_shaped_hooks(structured.get("value"))
        if hooks is not None:
            last_structured_hooks = hooks

    if last_structured_hooks is not None:
        return {"hooks": last_structured_hooks}

    assistant_texts = [
        m["assistant_message"]["content"]
        for m in messages
        if m.get("type") == "assistant_message" and m.get("assistant_message", {}).get("content")
    ]
    if not assistant_texts:
        return {}

    combined_text = "\n\n".join(assistant_texts)
    fenced_hooks = _hooks_from_fenced_json(combined_text)
    if fenced_hooks is not None:
        return {"hooks": fenced_hooks}

    return {"manus_message": combined_text}


def _resolve_dispatched() -> int:
    """Poll Manus for every task this node dispatched; report the terminal ones. Returns how many
    were resolved."""
    resolved = 0
    for operator_task_id, manus_task_id in list(state.all_dispatched().items()):
        manus_task = manus_client.get_task(manus_task_id)
        if manus_task is None:
            # Transient failure — leave in flight, retry next tick.
            continue

        if not manus_task.is_terminal:
            logger.info(
                "Task %s still in flight (Manus %s: %s)",
                operator_task_id,
                manus_task_id,
                manus_task.status,
            )
            continue

        result: Dict[str, Any] = {
            "manus_task_id": manus_task.task_id,
            "manus_status": manus_task.status,
            "task_url": manus_task.task_url,
            "credit_usage": manus_task.credit_usage,
        }
        result.update(_extract_manus_output(manus_task.task_id))

        if settings.DRY_RUN:
            logger.info(
                "[DRY-RUN] Would report %s -> %s (%s)",
                operator_task_id,
                manus_task.backend_status,
                result,
            )
            continue

        if backend_client.report_result(operator_task_id, manus_task.backend_status, result):
            state.forget(operator_task_id)
            resolved += 1
            logger.info(
                "Resolved %s -> %s (Manus %s)",
                operator_task_id,
                manus_task.backend_status,
                manus_task.status,
            )
    return resolved


def _dispatch_pending(pending: List[Dict[str, Any]]) -> int:
    """Claim and dispatch up to MAX_TASKS_PER_TICK pending tasks. Returns how many were dispatched."""
    dispatched = 0
    for task in pending[: settings.MAX_TASKS_PER_TICK]:
        operator_task_id = str(task.get("id") or "")
        if not operator_task_id:
            logger.error("Skipping a pending task with no id: %s", str(task)[:200])
            continue

        prompt = build_manus_prompt(task)
        title = build_manus_title(task)

        if settings.DRY_RUN:
            logger.info(
                "[DRY-RUN] Would dispatch %s (%s):\n%s",
                operator_task_id,
                task.get("task_type"),
                prompt[:600],
            )
            continue

        # Claim first. If the backend rejects the transition (already claimed by an overlapping
        # tick), do NOT create a Manus task — that would double-post.
        if not backend_client.mark_dispatched(operator_task_id):
            logger.warning("Could not claim %s — skipping (already claimed?).", operator_task_id)
            continue

        # Brecha B3 (2026-08-15): native structured_output_schema for research tasks so
        # hooks arrive via structured_output_result (deterministic) instead of the fenced
        # JSON fallback alone. Non-research tasks keep the schema unset.
        created = manus_client.create_task(
            content=prompt,
            title=title,
            structured_output_schema=(
                manus_client.RESEARCH_HOOKS_SCHEMA
                if (task.get("task_type") or "") == "research"
                else None
            ),
        )
        if created is None:
            # Claimed but not created. Left as `dispatched` with no sidecar entry, so it shows up
            # in list_orphans() for manual resolution rather than being silently re-run.
            logger.error(
                "Claimed %s but Manus task.create failed — task is now an orphan; "
                "resolve it manually.",
                operator_task_id,
            )
            continue

        state.remember(operator_task_id, created["task_id"])
        dispatched += 1
        logger.info(
            "Dispatched %s (%s) -> Manus %s (%s)",
            operator_task_id,
            task.get("task_type"),
            created["task_id"],
            created.get("task_url"),
        )
    return dispatched


def run_tick() -> Dict[str, int]:
    """Run one full tick. Returns a small summary for logging/tests."""
    if not manus_client.is_configured():
        # Fail closed BEFORE claiming anything (design.md D3): the scheduled task can be
        # registered before the founder creates the Manus API key, and stays inert until then.
        logger.error(
            "MANUS_API_KEY is not set — poller is inert. "
            "Set it in apps/hermes-manus-poller/.env to activate."
        )
        return {"resolved": 0, "dispatched": 0, "pending_seen": 0, "skipped": 1}

    resolved = _resolve_dispatched()

    pending = backend_client.list_pending()
    dispatched = _dispatch_pending(pending)

    # Surface anything the backend thinks is dispatched but this node has no Manus id for.
    orphans = state.list_orphans(
        [str(t.get("id")) for t in pending if t.get("status") == "dispatched"]
    )
    if orphans:
        logger.warning("Orphaned dispatched tasks with no local Manus id: %s", orphans)

    summary = {
        "resolved": resolved,
        "dispatched": dispatched,
        "pending_seen": len(pending),
        "skipped": 0,
    }
    logger.info("Tick complete: %s", summary)
    return summary
