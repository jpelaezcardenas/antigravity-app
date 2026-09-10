"""Follow-up cadence poller — one tick (taty-followup-cadence).

Flow per tick:
  1. Read NUEVOS crm_leads whose cadence isn't already complete (Supabase, direct)
  2. For each: compute elapsed hours since its anchor (last_inbound_at, or created_at if it
     never replied) and the next due cadence day, if any
  3. POST /internal/cadence/send-touch on Railway for each due lead ({lead_id, day} only — never
     a message string; the backend resolves and re-validates everything else)

Inert-without-config discipline (spec.md: "never a silent no-op that looks successful"): missing
INTERNAL_API_KEY or Supabase credentials logs an error and returns {"skipped": True, ...} rather
than quietly reporting zero due leads.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from cadence_rules import next_due_day
from config import settings

logger = logging.getLogger(__name__)


def _elapsed_hours(anchor_iso: Optional[str]) -> float:
    if not anchor_iso:
        return 0.0
    anchor = datetime.fromisoformat(anchor_iso.replace("Z", "+00:00"))
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - anchor).total_seconds() / 3600.0


def _send_touch(client: httpx.Client, lead_id: str, day: int) -> Dict[str, Any]:
    url = f"{settings.RAILWAY_BACKEND_URL}/internal/cadence/send-touch"
    headers = {"X-Internal-Api-Key": settings.INTERNAL_API_KEY}
    resp = client.post(
        url, json={"lead_id": lead_id, "day": day}, headers=headers,
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()


def run_tick() -> Dict[str, Any]:
    """Run one cadence-check tick."""
    if not settings.INTERNAL_API_KEY:
        logger.error("INTERNAL_API_KEY not set — poller is inert. Set it in .env")
        return {"skipped": True, "reason": "INTERNAL_API_KEY not configured"}

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — poller is inert.")
        return {"skipped": True, "reason": "Supabase credentials not configured"}

    from supabase_client import get_eligible_leads

    try:
        leads = get_eligible_leads(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY, settings.MAX_LEADS_PER_TICK
        )
    except Exception as exc:
        logger.error(f"Failed to read eligible leads: {exc}")
        return {"skipped": True, "reason": f"Supabase read failed: {exc}"}

    if not leads:
        logger.info("No eligible leads.")
        return {"leads_checked": 0, "touches_sent": 0, "touches_skipped": 0}

    logger.info(f"Checking {len(leads)} eligible lead(s) (dry_run={settings.DRY_RUN})")

    touches_sent = 0
    touches_skipped = 0

    with httpx.Client() as http_client:
        for lead in leads:
            lead_id = lead["id"]
            anchor = lead.get("last_inbound_at") or lead.get("created_at")
            elapsed = _elapsed_hours(anchor)
            due_day = next_due_day(lead.get("cadence_day"), elapsed)

            if due_day is None:
                continue

            if settings.DRY_RUN:
                logger.info(f"[dry-run] Would send day {due_day} touch to lead {lead_id}")
                touches_sent += 1
                continue

            try:
                result = _send_touch(http_client, lead_id, due_day)
                if result.get("sent"):
                    touches_sent += 1
                    logger.info(f"Sent day {due_day} touch to lead {lead_id}")
                else:
                    touches_skipped += 1
                    logger.info(
                        f"Day {due_day} touch NOT sent for lead {lead_id}: "
                        f"{result.get('reason')}"
                    )
            except httpx.HTTPStatusError as exc:
                touches_skipped += 1
                logger.error(
                    f"send-touch failed for lead {lead_id} — HTTP {exc.response.status_code}: "
                    f"{exc.response.text[:200]}"
                )
            except Exception as exc:
                touches_skipped += 1
                logger.error(f"send-touch failed for lead {lead_id}: {exc}")

    logger.info(
        f"Tick complete: {touches_sent} touch(es) sent, {touches_skipped} skipped/refused"
    )
    return {
        "leads_checked": len(leads),
        "touches_sent": touches_sent,
        "touches_skipped": touches_skipped,
    }
