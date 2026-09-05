"""
Siigo REST API client — read-only sync for Shadow GL ingestion.

Credentials per tenant are read from env vars:
  SIIGO_USERNAME_{tenant_id_no_dashes}  — e.g. user@empresa.com
  SIIGO_ACCESS_KEY_{tenant_id_no_dashes} — Siigo access_key (not the password)

Both vars must be present for a tenant to be eligible for sync.
Never stored in source or DB; retrieved from Railway env vars only.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_AUTH_PATH = "/auth"
_JOURNALS_PATH = "/v1/journals"
_INVOICES_PATH = "/v1/invoices"
_TOKEN_BUFFER_SECONDS = 60  # Refresh token this many seconds before expiry


class SiigoConfigurationError(RuntimeError):
    """Raised when Siigo is not configured well enough to make a real call."""


def _base_url() -> str:
    from config import settings
    return settings.SIIGO_BASE_URL


def _partner_id() -> str:
    """Return the configured Siigo Partner-Id, or fail closed.

    Siigo rejects requests whose Partner-Id is not a registered partner, so a wrong
    value fails at authentication anyway — but it fails as an opaque 401. Raising
    here instead makes the cause explicit and keeps an unverified guess out of the
    request. Set SIIGO_PARTNER_ID from Siigo's partner console.
    """
    from config import settings
    partner_id = (settings.SIIGO_PARTNER_ID or "").strip()
    if not partner_id:
        raise SiigoConfigurationError(
            "SIIGO_PARTNER_ID is not set. Siigo requires a registered Partner-Id header; "
            "obtain it from Siigo's partner console and set it as a Railway env var. "
            "Refusing to call the Siigo API with a guessed value."
        )
    return partner_id


def _env_key(tenant_id: str) -> tuple[str, str]:
    """Return (username_var, access_key_var) env var names for a tenant."""
    suffix = tenant_id.replace("-", "_").upper()
    return f"SIIGO_USERNAME_{suffix}", f"SIIGO_ACCESS_KEY_{suffix}"


def get_siigo_credentials(tenant_id: str) -> tuple[str, str] | None:
    """Return (username, access_key) for a tenant, or None if not configured."""
    username_var, key_var = _env_key(tenant_id)
    username = os.environ.get(username_var, "")
    access_key = os.environ.get(key_var, "")
    if not username or not access_key:
        return None
    return username, access_key


# NOTE: a list_siigo_eligible_tenants() helper was removed here — it had no callers and
# reconstructed UUIDs by slicing fixed character positions out of the env var name, which
# breaks on any name that is not exactly a 32-hex-with-underscores suffix. The poller
# discovers tenants from its own SIIGO_ELIGIBLE_TENANTS setting instead; the backend only
# ever resolves credentials for a tenant_id it is explicitly given.


class SiigoApiClient:
    """Thin async client for the Siigo REST API (read-only, per-tenant)."""

    def __init__(self, tenant_id: str, username: str, access_key: str) -> None:
        self.tenant_id = tenant_id
        self._username = username
        self._access_key = access_key
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    @classmethod
    def for_tenant(cls, tenant_id: str) -> "SiigoApiClient | None":
        """Build a client from env vars. Returns None if credentials are missing."""
        creds = get_siigo_credentials(tenant_id)
        if creds is None:
            return None
        username, access_key = creds
        return cls(tenant_id=tenant_id, username=username, access_key=access_key)

    def _token_is_valid(self) -> bool:
        if not self._token or not self._token_expires_at:
            return False
        now = datetime.now(tz=timezone.utc)
        return (self._token_expires_at - now).total_seconds() > _TOKEN_BUFFER_SECONDS

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        """POST /auth → cache JWT until near-expiry."""
        from datetime import timedelta
        payload = {"username": self._username, "access_key": self._access_key}
        headers = {"Partner-Id": _partner_id(), "Content-Type": "application/json"}
        resp = await client.post(f"{_base_url()}{_AUTH_PATH}", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
        logger.info(f"Siigo auth OK for tenant {self.tenant_id}, token valid {expires_in}s")

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Partner-Id": _partner_id(),
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _ensure_token(self, client: httpx.AsyncClient) -> None:
        if not self._token_is_valid():
            await self._authenticate(client)

    async def get_journals(
        self, start: date, end: date
    ) -> list[dict[str, Any]]:
        """Fetch journal entries for the date range and return Shadow GL row dicts."""
        async with httpx.AsyncClient(timeout=30) as client:
            await self._ensure_token(client)
            params = {
                "created_start": start.isoformat(),
                "created_end": end.isoformat(),
                "page_size": 100,
                "page": 1,
            }
            rows: list[dict[str, Any]] = []
            while True:
                resp = await client.get(
                    f"{_base_url()}{_JOURNALS_PATH}",
                    headers=self._auth_headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                for entry in results:
                    rows.extend(_journal_entry_to_rows(entry))
                # Pagination: stop when results < page_size
                if len(results) < params["page_size"]:
                    break
                params["page"] += 1
        return rows

    async def get_invoices(
        self, start: date, end: date
    ) -> list[dict[str, Any]]:
        """Fetch invoices for the date range and return Shadow GL row dicts."""
        async with httpx.AsyncClient(timeout=30) as client:
            await self._ensure_token(client)
            params = {
                "date_start": start.isoformat(),
                "date_end": end.isoformat(),
                "page_size": 100,
                "page": 1,
            }
            rows: list[dict[str, Any]] = []
            while True:
                resp = await client.get(
                    f"{_base_url()}{_INVOICES_PATH}",
                    headers=self._auth_headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                for invoice in results:
                    rows.extend(_invoice_to_rows(invoice))
                if len(results) < params["page_size"]:
                    break
                params["page"] += 1
        return rows

    async def sync_to_shadow_gl(self, days_back: int = 1) -> dict[str, Any]:
        """Pull journals + invoices and ingest them into the Shadow GL.

        Returns a summary dict: {rows_ingested, date_range, errors}.
        Always passes is_verified_real=True — this is live client data.
        """
        from datetime import timedelta
        from services.shadow_gl_service import ingest_siigo_csv
        from presentation.shadow_gl_endpoints import _rows_to_csv_text

        today = date.today()
        start = today - timedelta(days=days_back)

        all_rows: list[dict[str, Any]] = []
        errors: list[str] = []

        try:
            journal_rows = await self.get_journals(start, today)
            all_rows.extend(journal_rows)
        except Exception as exc:
            errors.append(f"journals: {exc}")
            logger.error(f"Siigo journals failed for tenant {self.tenant_id}: {exc}")

        try:
            invoice_rows = await self.get_invoices(start, today)
            all_rows.extend(invoice_rows)
        except Exception as exc:
            errors.append(f"invoices: {exc}")
            logger.error(f"Siigo invoices failed for tenant {self.tenant_id}: {exc}")

        if not all_rows:
            return {"rows_ingested": 0, "date_range": "", "errors": errors}

        csv_text = _rows_to_csv_text(all_rows)
        success, summary, error = await ingest_siigo_csv(
            self.tenant_id, csv_text, is_verified_real=True
        )
        if not success:
            errors.append(f"ingest: {error}")
            return {"rows_ingested": 0, "date_range": "", "errors": errors}

        return {
            "rows_ingested": summary.get("row_count", 0),
            "date_range": summary.get("date_range", ""),
            "errors": errors,
        }


def _journal_entry_to_rows(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Map a Siigo journal entry to Shadow GL row shape(s)."""
    rows: list[dict[str, Any]] = []
    ref = entry.get("id") or entry.get("consecutive") or "UNKNOWN"
    entry_date = entry.get("date", "")[:10]  # ISO date, truncate time
    items = entry.get("items") or []
    for item in items:
        account_code = str(item.get("account", {}).get("code", ""))
        description = item.get("description", "")
        debit = item.get("debit", 0) or 0
        credit = item.get("credit", 0) or 0
        rows.append({
            "fecha": entry_date,
            "referencia_externa": str(ref),
            "codigo_cuenta": account_code,
            "descripcion": description,
            "debito_cents": int(round(float(debit) * 100)),
            "credito_cents": int(round(float(credit) * 100)),
        })
    return rows


def _invoice_to_rows(invoice: dict[str, Any]) -> list[dict[str, Any]]:
    """Map a Siigo invoice to Shadow GL row shape (AR debit + revenue credit)."""
    ref = str(invoice.get("id") or invoice.get("consecutive") or "INV")
    invoice_date = (invoice.get("date") or "")[:10]
    total = float(invoice.get("total", 0) or 0)
    total_cents = int(round(total * 100))
    if total_cents == 0:
        return []
    return [
        {
            "fecha": invoice_date,
            "referencia_externa": f"INV-{ref}",
            "codigo_cuenta": "1300",  # Accounts Receivable (DIAN PUC)
            "descripcion": f"Invoice {ref}",
            "debito_cents": total_cents,
            "credito_cents": 0,
        },
        {
            "fecha": invoice_date,
            "referencia_externa": f"INV-{ref}",
            "codigo_cuenta": "4100",  # Sales Revenue (DIAN PUC)
            "descripcion": f"Invoice {ref}",
            "debito_cents": 0,
            "credito_cents": total_cents,
        },
    ]
