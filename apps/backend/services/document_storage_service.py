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
        # Real bug found live 2026-09-11 (task 6b), twice over. First: file_options=
        # {"upsert": "true"} is not honored at all by the storage3 version this repo's
        # requirements.txt actually pins (storage3>=0.5.3,<0.7.0, transitively via
        # supabase==2.0.3, confirmed by downloading and reading that exact wheel — this repo's
        # local dev venv has storage3 2.31.0 installed, a completely different, much newer major
        # version, which is why this looked fine locally). Second attempted fix used
        # bucket.update(), which doesn't exist as a method at all in the pinned version either —
        # same dev/prod drift trap, different method. The pinned version's file_api.py has exactly
        # two relevant primitives: upload() (plain POST, no upsert semantics) and remove() (bulk
        # DELETE by path list, present in effectively every storage3 version as a basic
        # operation). So: on a duplicate-key error, remove the existing object first, then upload
        # again — never assume any convenience method (update/upsert) exists without having read
        # the actual pinned source.
        error_payload = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
        if error_payload.get("code") != "KeyAlreadyExists":
            raise
        bucket.remove([path])
        bucket.upload(path, file_bytes, {"content-type": mime_type})
    return path


def get_signed_document_url(storage_path: str) -> str:
    """Generates a short-lived signed URL for a stored document — never a permanent/public URL."""
    client = get_service_supabase()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(
        storage_path, _SIGNED_URL_EXPIRY_SECONDS
    )
    return result["signedURL"]
