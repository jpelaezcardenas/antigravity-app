"""Tax document storage service (taty-document-collection, Change I).

First Supabase Storage-using service in this repo. Stores RUT/extractos documents collected by
Taty via WhatsApp in the private crm-tax-documents bucket (see migration 0026 +
design.md Decision 3). File names are stable and predictable ({lead_id}/{document_type}.{ext}) —
never persisted as URLs; signed URLs are generated on demand and expire.
"""

from __future__ import annotations

from typing import Literal

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
    client.storage.from_(BUCKET_NAME).upload(
        path, file_bytes, {"content-type": mime_type, "upsert": "true"}
    )
    return path


def get_signed_document_url(storage_path: str) -> str:
    """Generates a short-lived signed URL for a stored document — never a permanent/public URL."""
    client = get_service_supabase()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(
        storage_path, _SIGNED_URL_EXPIRY_SECONDS
    )
    return result["signedURL"]
