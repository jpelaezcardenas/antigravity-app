"""Tax document storage service (taty-document-collection, Change I).

First Supabase Storage-using service in this repo. Stores RUT/extractos documents collected by
Taty via WhatsApp in the private crm-tax-documents bucket (see migration 0026 +
design.md Decision 3). File names are stable and predictable ({lead_id}/{document_type}.{ext}) —
never persisted as URLs; signed URLs are generated on demand and expire.
"""

from __future__ import annotations

from typing import Literal

from storage3.utils import StorageException

from core.supabase_client import get_service_supabase

BUCKET_NAME = "crm-tax-documents"

_SIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour

_MIME_TO_EXTENSION = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
}


def _extension_for_mime_type(mime_type: str) -> str:
    return _MIME_TO_EXTENSION.get(mime_type, "bin")


def upload_tax_document(
    lead_id: str,
    document_type: Literal["rut", "extractos"],
    file_bytes: bytes,
    mime_type: str,
) -> str:
    """Uploads a document to the private crm-tax-documents bucket and returns its storage path
    ({lead_id}/{document_type}.{ext})."""
    extension = _extension_for_mime_type(mime_type)
    path = f"{lead_id}/{document_type}.{extension}"

    client = get_service_supabase()
    bucket = client.storage.from_(BUCKET_NAME)
    try:
        bucket.upload(path, file_bytes, {"content-type": mime_type, "upsert": "true"})
    except StorageException as exc:
        # Real bug found live 2026-09-11 (task 6b): file_options={"upsert": "true"} is only
        # honored by some storage3 versions (confirmed: the one this repo's requirements.txt
        # actually pins, supabase==2.0.3, does NOT honor it — a retry against a path that already
        # has a file from an earlier attempt raised 'KeyAlreadyExists' in production despite this
        # option being set). Rather than guess the right upsert-string format for whichever
        # version is actually installed, fall back to the unconditional PUT (update()), which
        # every storage3 version supports as a real distinct HTTP verb — not an option string that
        # can silently stop being honored across a dependency upgrade.
        error_payload = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
        if error_payload.get("code") != "KeyAlreadyExists":
            raise
        bucket.update(path, file_bytes, {"content-type": mime_type})
    return path


def get_signed_document_url(storage_path: str) -> str:
    """Generates a short-lived signed URL for a stored document — never a permanent/public URL."""
    client = get_service_supabase()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(
        storage_path, _SIGNED_URL_EXPIRY_SECONDS
    )
    return result["signedURL"]
