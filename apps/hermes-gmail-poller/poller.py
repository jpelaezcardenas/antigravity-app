"""Gmail attachment ingestion poller — one tick.

Flow per tick:
  1. List INBOX messages with attachments not yet labeled 'contexia-processed'
  2. For each: extract sender, resolve tenant via gmail_sender_map (Supabase)
  3. Download each supported attachment
  4. POST /internal/ingest/file on Railway (multipart, INTERNAL_API_KEY auth)
  5. Label the message 'contexia-processed' and mark read

Emails from unregistered senders are skipped (logged, NOT labeled — so they can be
processed later once the sender is added to gmail_sender_map).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _post_attachment(
    client: httpx.Client, tenant_id: str, filename: str, content: bytes, mime_type: str
) -> dict[str, Any]:
    """POST one attachment to /internal/ingest/file."""
    url = f"{settings.RAILWAY_BACKEND_URL}/internal/ingest/file"
    files = {"file": (filename, content, mime_type)}
    data = {"tenant_id": tenant_id, "is_verified_real": "true"}
    headers = {"X-Internal-Api-Key": settings.INTERNAL_API_KEY}

    resp = client.post(
        url, files=files, data=data, headers=headers, timeout=settings.HTTP_TIMEOUT_SECONDS
    )
    resp.raise_for_status()
    return resp.json()


def run_tick() -> dict[str, Any]:
    """Run one Gmail ingestion tick."""
    if not settings.INTERNAL_API_KEY:
        logger.error("INTERNAL_API_KEY not set — poller is inert. Set it in .env")
        return {"skipped": True, "reason": "INTERNAL_API_KEY not configured"}

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — poller is inert.")
        return {"skipped": True, "reason": "Supabase credentials not configured"}

    from gmail_client import GmailClient
    from supabase_client import get_tenant_id_for_sender

    gmail = GmailClient(settings.GMAIL_OAUTH_TOKEN_PATH, settings.GMAIL_CREDENTIALS_PATH)

    try:
        messages = gmail.list_unprocessed_messages(
            settings.GMAIL_PROCESSED_LABEL, settings.MAX_ATTACHMENTS_PER_TICK
        )
    except Exception as exc:
        logger.error(f"Failed to list Gmail messages: {exc}")
        return {"skipped": True, "reason": f"Gmail list failed: {exc}"}

    if not messages:
        logger.info("No unprocessed messages with attachments.")
        return {"messages": 0, "attachments_ingested": 0, "rows_ingested": 0, "skipped_senders": []}

    logger.info(f"Found {len(messages)} unprocessed message(s) (dry_run={settings.DRY_RUN})")

    total_attachments = 0
    total_rows = 0
    skipped_senders: list[str] = []
    supported = settings.supported_mime_types_list

    with httpx.Client() as http_client:
        for msg_ref in messages:
            message_id = msg_ref["id"]
            try:
                full = gmail.get_message_full(message_id)
            except Exception as exc:
                logger.error(f"Failed to fetch message {message_id}: {exc}")
                continue

            sender = gmail.extract_sender(full)
            if not sender:
                logger.warning(f"Message {message_id}: could not extract sender, skipping")
                continue

            tenant_id = get_tenant_id_for_sender(
                sender, settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
            )
            if not tenant_id:
                logger.info(f"Message {message_id} from {sender}: no tenant mapping, skipping (not labeled)")
                skipped_senders.append(sender)
                continue

            attachments = gmail.list_attachments(full, supported)
            if not attachments:
                logger.info(f"Message {message_id} from {sender}: no supported attachments")
                continue

            message_ok = True
            for part in attachments:
                filename = part["filename"]
                mime_type = part.get("mimeType", "application/octet-stream")
                attachment_id = part["body"]["attachmentId"]

                if settings.DRY_RUN:
                    logger.info(
                        f"[dry-run] Would ingest {filename} ({mime_type}) "
                        f"from {sender} → tenant {tenant_id}"
                    )
                    total_attachments += 1
                    continue

                try:
                    content = gmail.download_attachment(message_id, attachment_id)
                    result = _post_attachment(http_client, tenant_id, filename, content, mime_type)
                    rows = result.get("row_count", 0)
                    total_rows += rows
                    total_attachments += 1
                    logger.info(f"Ingested {filename} from {sender}: {rows} rows → tenant {tenant_id}")
                except httpx.HTTPStatusError as exc:
                    message_ok = False
                    logger.error(
                        f"Ingest failed for {filename} — HTTP {exc.response.status_code}: "
                        f"{exc.response.text[:200]}"
                    )
                except Exception as exc:
                    message_ok = False
                    logger.error(f"Ingest failed for {filename}: {exc}")

            # Only label as processed if every attachment succeeded — a failed one
            # stays unlabeled so the next tick retries it.
            if message_ok and not settings.DRY_RUN:
                try:
                    gmail.mark_processed(message_id, settings.GMAIL_PROCESSED_LABEL)
                except Exception as exc:
                    logger.error(f"Failed to label message {message_id}: {exc}")

    logger.info(
        f"Tick complete: {total_attachments} attachment(s), {total_rows} rows ingested, "
        f"{len(skipped_senders)} sender(s) unmapped"
    )

    return {
        "messages": len(messages),
        "attachments_ingested": total_attachments,
        "rows_ingested": total_rows,
        "skipped_senders": skipped_senders,
    }
