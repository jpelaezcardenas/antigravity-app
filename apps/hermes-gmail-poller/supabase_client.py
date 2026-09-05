"""Supabase client for the gmail-poller — reads gmail_sender_map."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_tenant_id_for_sender(sender_email: str, supabase_url: str, service_role_key: str) -> Optional[str]:
    """Look up the tenant_id for a sender email in gmail_sender_map.

    Returns None if the sender is not registered (email not onboarded).
    """
    try:
        from supabase import create_client
    except ImportError as exc:
        raise ImportError("pip install supabase") from exc

    client = create_client(supabase_url, service_role_key)
    resp = (
        client.table("gmail_sender_map")
        .select("tenant_id")
        .eq("sender_email", sender_email.lower())
        .maybe_single()
        .execute()
    )
    if resp.data:
        return resp.data["tenant_id"]
    logger.warning(f"No tenant mapping found for sender: {sender_email}")
    return None
