"""Supabase client for the cadence-poller — reads crm_leads eligible for follow-up.

Mirrors apps/hermes-gmail-poller/supabase_client.py's shape (a plain module-level function, no
class, imports the `supabase` package lazily so importing this module never requires it)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_eligible_leads(
    supabase_url: str, service_role_key: str, limit: int
) -> List[Dict[str, Any]]:
    """Returns NUEVOS leads whose cadence isn't already complete, with only the fields the
    poller's due-day computation needs. Eligibility (stage, cadence_completed_at) is filtered
    here as a cheap pre-pass; the backend endpoint re-checks both authoritatively before ever
    sending — this is never the sole gate."""
    try:
        from supabase import create_client
    except ImportError as exc:
        raise ImportError("pip install supabase") from exc

    client = create_client(supabase_url, service_role_key)
    resp = (
        client.table("crm_leads")
        .select("id, cadence_day, last_inbound_at, created_at")
        .eq("stage", "NUEVOS")
        .is_("cadence_completed_at", "null")
        .limit(limit)
        .execute()
    )
    return resp.data or []
