"""One tick of the Hermes->HubSpot sync loop.

Supabase stays authoritative and this sync is strictly one-way (design.md Goals). Two
independent passes per tick:
  1. crm_leads -> HubSpot Contact + Deal (single default pipeline, funnel-mapped dealstage)
  2. b2b_clients -> HubSpot Company ONLY — never a Deal (design.md Decision #5)

Idempotent by construction: a row with an existing hubspot_*_id is upserted (PATCH) by that id,
never re-created, so re-running a tick never duplicates records.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import chatwoot_client
import hubspot_client
import supabase_client
from config import settings
from stage_mapping import resolve_dealstage

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sync_lead(lead: Dict[str, Any]) -> bool:
    lead_id = str(lead.get("id") or "")
    if not lead_id:
        logger.error("Skipping a crm_leads row with no id: %s", str(lead)[:200])
        return False

    is_first_sync = not lead.get("hubspot_contact_id")

    contact_properties = {
        "firstname": (lead.get("full_name") or "").split(" ", 1)[0] or None,
        "lastname": (lead.get("full_name") or "").split(" ", 1)[1] if " " in (lead.get("full_name") or "") else None,
        "email": lead.get("email"),
        "phone": lead.get("whatsapp_phone"),
    }
    contact_id = hubspot_client.upsert_contact(lead.get("hubspot_contact_id"), contact_properties)
    if contact_id is None:
        logger.error("Failed to upsert HubSpot Contact for lead %s", lead_id)
        return False

    # hubspot-activity-value-sync: log the conversation once, on first sync only (design.md
    # Decision #1) — avoids spamming an identical Note every 5-min tick.
    last_message = lead.get("last_message")
    if is_first_sync and last_message:
        hubspot_client.create_note(contact_id, last_message)

    wompi_tx = supabase_client.get_latest_wompi_transaction(lead_id)
    dealstage = resolve_dealstage(
        lead_stage=lead.get("stage") or "NUEVOS",
        wompi_status=(wompi_tx or {}).get("status"),
    )
    deal_properties = {
        "dealname": lead.get("full_name") or f"Lead {lead_id}",
        "pipeline": settings.HUBSPOT_DEAL_PIPELINE,
        "dealstage": dealstage,
    }
    amount_cents = (wompi_tx or {}).get("amount_cents")
    if amount_cents is not None:
        deal_properties["amount"] = str(amount_cents / 100)
    deal_id = hubspot_client.upsert_deal(lead.get("hubspot_deal_id"), deal_properties)
    if deal_id is None:
        logger.error("Failed to upsert HubSpot Deal for lead %s", lead_id)
        return False

    # hubspot-activity-value-sync: a lead awaiting payment approval gets a visible follow-up
    # Task in HubSpot, gated on not already having one open (design.md Decision #3).
    if lead.get("stage") == "POR_APROBAR" and not hubspot_client.has_open_task(deal_id):
        hubspot_client.create_task(deal_id, f"Aprobar pago — {lead.get('full_name') or lead_id}")

    # chatwoot-hubspot-supabase-cross-ids: best-effort — a Chatwoot blip must never block
    # persisting the HubSpot sync itself (spec.md "Chatwoot failure does not block").
    try:
        phone = lead.get("whatsapp_phone")
        if phone:
            chatwoot_contact_id = chatwoot_client.find_contact_by_phone(phone)
            if chatwoot_contact_id is not None:
                chatwoot_client.set_cross_reference_attributes(
                    chatwoot_contact_id, lead_id, contact_id
                )
    except Exception:
        logger.exception("Chatwoot cross-reference push failed for lead %s (non-fatal)", lead_id)

    return supabase_client.mark_lead_synced(lead_id, contact_id, deal_id, _now_iso())


def _sync_b2b_client(client: Dict[str, Any]) -> bool:
    client_id = str(client.get("id") or "")
    if not client_id:
        logger.error("Skipping a b2b_clients row with no id: %s", str(client)[:200])
        return False

    company_properties = {
        "name": client.get("contact_name") or client.get("legal_name") or f"Client {client_id}",
        "phone": client.get("phone"),
    }
    company_id = hubspot_client.upsert_company(client.get("hubspot_company_id"), company_properties)
    if company_id is None:
        logger.error("Failed to upsert HubSpot Company for b2b_client %s", client_id)
        return False

    # Deliberately no Deal is ever created here (design.md Decision #5) — B2B never touches
    # the single free-tier pipeline.
    return supabase_client.mark_b2b_client_synced(client_id, company_id, _now_iso())


def sync_leads() -> int:
    """Syncs up to MAX_RECORDS_PER_TICK crm_leads rows (every tick, all rows — see design.md
    Decision #7). Returns how many succeeded."""
    leads = supabase_client.list_leads(settings.MAX_RECORDS_PER_TICK)
    if settings.DRY_RUN:
        logger.info("[DRY-RUN] Would sync %d lead(s)", len(leads))
        return 0
    return sum(1 for lead in leads if _sync_lead(lead))


def sync_b2b_clients() -> int:
    """Syncs up to MAX_RECORDS_PER_TICK b2b_clients rows (every tick, all rows — see design.md
    Decision #7). Returns how many succeeded."""
    clients = supabase_client.list_b2b_clients(settings.MAX_RECORDS_PER_TICK)
    if settings.DRY_RUN:
        logger.info("[DRY-RUN] Would sync %d b2b client(s)", len(clients))
        return 0
    return sum(1 for client in clients if _sync_b2b_client(client))


def run_tick() -> Dict[str, int]:
    """Runs one full tick. Returns a small summary for logging/tests."""
    if not hubspot_client.is_configured() or not supabase_client.is_configured():
        logger.error(
            "HUBSPOT_ACCESS_TOKEN and/or SUPABASE_SERVICE_ROLE_KEY not set — poller is inert. "
            "Set them in apps/hermes-hubspot-poller/.env to activate."
        )
        return {"leads_synced": 0, "b2b_clients_synced": 0, "skipped": 1}

    leads_synced = sync_leads()
    b2b_clients_synced = sync_b2b_clients()

    summary = {"leads_synced": leads_synced, "b2b_clients_synced": b2b_clients_synced, "skipped": 0}
    logger.info("Tick complete: %s", summary)
    return summary
