"""
Shadow GL Service

Parses DIAN UBL 2.1 XML documents (invoices, credit notes, debit notes) and
ingests them into `dian_xml_documents`. Ingestion is currently triggered by
manual upload (POST /api/v1/shadow-gl/dian-xml/ingest); a live DIAN webhook
is a later, additive trigger onto the same parser (see design.md Slice 2
decision, 2026-06-21).
"""

from __future__ import annotations

import csv
import io
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

UBL_NAMESPACES = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

DOCUMENT_TYPE_BY_ROOT_TAG = {
    "Invoice": "invoice",
    "CreditNote": "credit_note",
    "DebitNote": "debit_note",
}


class DianXmlParseError(ValueError):
    """Raised when a DIAN UBL 2.1 document is malformed or missing required fields."""


class SiigoCsvParseError(ValueError):
    """Raised when a Siigo CSV export is malformed or missing required fields."""


class ApprovalQueueError(Exception):
    """Raised when approval_queue operation fails."""


def _to_minor_units(amount_text: Optional[str]) -> int:
    if not amount_text:
        return 0
    try:
        return int((Decimal(amount_text) * 100).to_integral_value())
    except InvalidOperation as exc:
        raise DianXmlParseError(f"Invalid monetary amount: {amount_text!r}") from exc


def parse_dian_ubl_xml(raw_xml: str) -> Dict[str, Any]:
    """
    Parse a DIAN UBL 2.1 XML document into the fields stored in
    `dian_xml_documents`.

    Raises:
        DianXmlParseError: if the XML is malformed or required fields are missing.
    """
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise DianXmlParseError(f"Malformed XML: {exc}") from exc

    local_tag = root.tag.split("}")[-1]
    document_type = DOCUMENT_TYPE_BY_ROOT_TAG.get(local_tag)
    if document_type is None:
        raise DianXmlParseError(
            f"Unsupported root element <{local_tag}>; expected Invoice, CreditNote, or DebitNote"
        )

    def find_text(path: str) -> Optional[str]:
        el = root.find(path, UBL_NAMESPACES)
        return el.text.strip() if el is not None and el.text else None

    cufe = find_text("cbc:UUID")
    issue_date = find_text("cbc:IssueDate")
    issuer_nit = find_text(
        "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID"
    )
    receiver_nit = find_text(
        "cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID"
    )
    total_amount_text = find_text("cac:LegalMonetaryTotal/cbc:PayableAmount")
    tax_amount_text = find_text("cac:TaxTotal/cbc:TaxAmount")
    withholding_amount_text = find_text("cac:WithholdingTaxTotal/cbc:TaxAmount")

    missing = [
        name
        for name, value in [
            ("cbc:UUID (CUFE)", cufe),
            ("cbc:IssueDate", issue_date),
            ("AccountingSupplierParty NIT", issuer_nit),
            ("AccountingCustomerParty NIT", receiver_nit),
            ("LegalMonetaryTotal/PayableAmount", total_amount_text),
        ]
        if not value
    ]
    if missing:
        raise DianXmlParseError(f"Missing required field(s): {', '.join(missing)}")

    currency_el = root.find("cac:LegalMonetaryTotal/cbc:PayableAmount", UBL_NAMESPACES)
    currency_code = (
        currency_el.attrib.get("currencyID", "COP") if currency_el is not None else "COP"
    )

    return {
        "cufe": cufe,
        "document_type": document_type,
        "issuer_nit": issuer_nit,
        "receiver_nit": receiver_nit,
        "issue_date": issue_date,
        "total_amount_minor": _to_minor_units(total_amount_text),
        "tax_amount_minor": _to_minor_units(tax_amount_text),
        "withholding_amount_minor": _to_minor_units(withholding_amount_text),
        "currency_code": currency_code,
    }


def parse_siigo_csv(csv_text: str) -> List[Dict[str, Any]]:
    """
    Parse a Siigo journal export CSV into journal entries + lines.

    CSV format expected (Siigo standard export):
    - transaction_date: ISO 8601 (YYYY-MM-DD)
    - account_code: GL account code (e.g., 1105)
    - debit_amount: numeric string (e.g., "850000.00")
    - credit_amount: numeric string or empty
    - memo: transaction description
    - external_reference_id: Siigo document/voucher ID (e.g., DOC-001, TRF-050)
    - currency_code: ISO 4217 (e.g., COP, USD)

    Returns:
        List of dicts, grouped by external_reference_id:
        [
            {
                "external_reference_id": "DOC-001",
                "transaction_date": "2026-06-18",
                "lines": [
                    {"account_code": "1105", "debit_minor": 85000000, "credit_minor": 0, "memo": "..."},
                    {"account_code": "4105", "debit_minor": 0, "credit_minor": 85000000, "memo": "..."}
                ]
            }
        ]

    Raises:
        SiigoCsvParseError: if CSV is malformed or required fields missing.
    """
    if not csv_text.strip():
        return []

    try:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        if reader.fieldnames is None:
            raise SiigoCsvParseError("CSV is empty or has no headers")

        required_cols = {
            "transaction_date",
            "account_code",
            "debit_amount",
            "credit_amount",
            "memo",
            "external_reference_id",
            "currency_code",
        }
        missing = required_cols - set(reader.fieldnames)
        if missing:
            raise SiigoCsvParseError(f"Missing required column(s): {', '.join(sorted(missing))}")

        entries_by_ref: Dict[str, Dict[str, Any]] = {}

        for row_num, row in enumerate(reader, start=2):
            try:
                ref_id = row["external_reference_id"].strip()
                txn_date = row["transaction_date"].strip()
                account_code = row["account_code"].strip()
                memo = row["memo"].strip()
                currency_code = row["currency_code"].strip() or "COP"

                # Validate date is ISO 8601
                try:
                    datetime.fromisoformat(txn_date)
                except ValueError:
                    raise SiigoCsvParseError(
                        f"Row {row_num}: Invalid date format '{txn_date}'; expected ISO 8601 (YYYY-MM-DD)"
                    )

                debit_str = row["debit_amount"].strip() or None
                credit_str = row["credit_amount"].strip() or None

                debit_minor = _to_minor_units(debit_str) if debit_str else 0
                credit_minor = _to_minor_units(credit_str) if credit_str else 0

                if debit_minor < 0 or credit_minor < 0:
                    raise SiigoCsvParseError(
                        f"Row {row_num}: Negative amounts not allowed (debit={debit_str}, credit={credit_str})"
                    )

                # Group by external_reference_id
                if ref_id not in entries_by_ref:
                    entries_by_ref[ref_id] = {
                        "external_reference_id": ref_id,
                        "transaction_date": txn_date,
                        "lines": [],
                    }

                line = {
                    "account_code": account_code,
                    "debit_minor": debit_minor,
                    "credit_minor": credit_minor,
                    "currency_code": currency_code,
                    "memo": memo,
                }
                entries_by_ref[ref_id]["lines"].append(line)

            except SiigoCsvParseError:
                raise
            except (KeyError, ValueError) as exc:
                raise SiigoCsvParseError(f"Row {row_num}: {exc}") from exc

        # Verify each entry is balanced
        for ref_id, entry in entries_by_ref.items():
            debit_sum = sum(line["debit_minor"] for line in entry["lines"])
            credit_sum = sum(line["credit_minor"] for line in entry["lines"])
            if debit_sum != credit_sum:
                raise SiigoCsvParseError(
                    f"Entry {ref_id}: imbalanced (debit={debit_sum}, credit={credit_sum})"
                )

        return list(entries_by_ref.values())

    except csv.Error as exc:
        raise SiigoCsvParseError(f"CSV parse error: {exc}") from exc
    except SiigoCsvParseError:
        raise
    except Exception as exc:
        raise SiigoCsvParseError(f"Unexpected error parsing CSV: {exc}") from exc


async def _create_approval_queue(
    tenant_id: str,
    action_type: str,
    error: str,
    raw_input: str,
) -> str:
    """
    Create an approval_queue record for a parsing error.

    Args:
        tenant_id: Tenant UUID
        action_type: Action type (e.g., "review_accounting_entry")
        error: Error message
        raw_input: Raw CSV or XML that failed parsing

    Returns:
        approval_queue.id (UUID as string)

    Raises:
        ApprovalQueueError: if insertion fails
    """
    import uuid as uuid_lib

    supabase = get_supabase()

    queue_data = {
        "tenant_id": tenant_id,
        "draft_id": f"approval-{uuid_lib.uuid4().hex[:8]}",  # Unique draft_id
        "draft_type": action_type,  # e.g., "review_accounting_entry"
        "status": "pending",
        "reason": error,  # Store error message as reason
        "approved_by": "",  # Empty until approval (NOT NULL constraint)
        "payload": {
            "error": error,
            "raw_input": raw_input,
            "timestamp": datetime.now(tz=None).isoformat(),
        },
        "vectorization_status": "pending",  # NOT NULL constraint
    }

    try:
        result = supabase.table("approval_queue").insert(queue_data).execute()
        queue_id = result.data[0]["id"]
        logger.info(f"Created approval_queue {queue_id} for tenant {tenant_id}")
        return queue_id
    except Exception as exc:
        logger.error(f"Failed to create approval_queue: {exc}")
        raise ApprovalQueueError(f"Failed to create approval_queue: {exc}") from exc


async def _get_approval_queue(queue_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch approval_queue row by ID.

    Args:
        queue_id: approval_queue.id

    Returns:
        Approval queue row dict, or None if not found
    """
    supabase = get_supabase()
    try:
        result = supabase.table("approval_queue").select("*").eq("id", queue_id).execute()
        return result.data[0] if result.data else None
    except Exception as exc:
        logger.error(f"Failed to get approval_queue {queue_id}: {exc}")
        return None


async def _update_approval_queue(
    queue_id: str,
    status: str,
    reviewer_id: Optional[str] = None,
    reason: str = "",
    reviewed_at: Optional[str] = None,
) -> bool:
    """
    Update approval_queue after approval decision from Hermes.

    Args:
        queue_id: approval_queue.id
        status: "approved" or "rejected"
        reviewer_id: User ID who made the decision
        reason: Why approved/rejected
        reviewed_at: ISO timestamp of decision

    Returns:
        True if updated successfully, False otherwise
    """
    supabase = get_supabase()

    update_data = {
        "status": status,
        "reason": reason,
    }
    if reviewer_id:
        update_data["approved_by"] = reviewer_id
    if reviewed_at:
        update_data["updated_at"] = reviewed_at

    try:
        result = supabase.table("approval_queue").update(update_data).eq("id", queue_id).execute()
        success = len(result.data) > 0
        if success:
            logger.info(f"Updated approval_queue {queue_id} to {status}")
        return success
    except Exception as exc:
        logger.error(f"Failed to update approval_queue {queue_id}: {exc}")
        return False


async def ingest_siigo_csv(
    tenant_id: str, csv_text: str
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse and persist a Siigo CSV journal export for a tenant.

    Idempotent on (tenant_id, external_reference_id, entry_date): re-ingesting
    the same batch returns success without duplicating.

    Returns:
        (success, summary_dict, error)
        where summary_dict = {"row_count": N, "date_range": "YYYY-MM-DD..YYYY-MM-DD"}
    """
    try:
        entries = parse_siigo_csv(csv_text)
    except SiigoCsvParseError as exc:
        logger.warning(f"Siigo CSV parse failed: {exc}")
        # Phase 6: Create approval_queue instead of returning error 400
        try:
            queue_id = await _create_approval_queue(
                tenant_id=tenant_id,
                action_type="review_accounting_entry",
                error=str(exc),
                raw_input=csv_text,
            )
            logger.info(f"Created approval_queue {queue_id} for parsing error")
            return False, {"queue_id": queue_id}, str(exc)
        except ApprovalQueueError as queue_exc:
            # Fallback: if approval_queue creation fails, return error
            logger.error(f"Failed to create approval_queue: {queue_exc}")
            return False, None, str(exc)

    if not entries:
        return True, {"row_count": 0, "date_range": ""}, None

    supabase = get_supabase()
    row_count = 0
    dates = set()

    try:
        for entry in entries:
            ref_id = entry["external_reference_id"]
            txn_date = entry["transaction_date"]
            dates.add(txn_date)
            lines = entry["lines"]

            # Check if entry already exists (idempotency)
            existing = (
                supabase.table("erp_journal_entries")
                .select("id")
                .eq("tenant_id", tenant_id)
                .eq("external_reference_id", ref_id)
                .eq("entry_date", txn_date)
                .execute()
            )
            if existing.data:
                logger.info(
                    f"Entry {ref_id} on {txn_date} already ingested for tenant {tenant_id}; skipping"
                )
                continue

            # Insert journal entry
            entry_data = {
                "tenant_id": tenant_id,
                "external_reference_id": ref_id,
                "entry_date": txn_date,
                "memo": f"Siigo import: {ref_id}",
                "source": "siigo_csv",
                "uploaded_at": datetime.now(tz=None).isoformat(),
            }
            inserted_entry = supabase.table("erp_journal_entries").insert(entry_data).execute()
            entry_id = inserted_entry.data[0]["id"]
            row_count += 1

            # Insert journal lines
            line_data = [
                {
                    "entry_id": entry_id,
                    "tenant_id": tenant_id,
                    "account_code": line["account_code"],
                    "debit_minor": line["debit_minor"],
                    "credit_minor": line["credit_minor"],
                    "currency_code": line["currency_code"],
                    "memo": line["memo"],
                }
                for line in lines
            ]
            supabase.table("erp_journal_lines").insert(line_data).execute()

        # Build date range
        if dates:
            date_list = sorted(dates)
            date_range = f"{date_list[0]}..{date_list[-1]}"
        else:
            date_range = ""

        return True, {"row_count": row_count, "date_range": date_range}, None

    except Exception as exc:
        logger.error(f"Siigo CSV insert failed: {exc}")
        return False, None, str(exc)


async def ingest_dian_xml(
    tenant_id: str, raw_xml: str
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse and persist a DIAN UBL 2.1 XML document for a tenant.

    Idempotent on (tenant_id, cufe): re-ingesting the same CUFE returns the
    existing row instead of raising or duplicating.

    Returns:
        (success, document_row, error)
    """
    try:
        parsed = parse_dian_ubl_xml(raw_xml)
    except DianXmlParseError as exc:
        logger.warning(f"DIAN XML parse failed: {exc}")
        return False, None, str(exc)

    supabase = get_supabase()

    existing = (
        supabase.table("dian_xml_documents")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("cufe", parsed["cufe"])
        .execute()
    )
    if existing.data:
        logger.info(f"CUFE {parsed['cufe']} already ingested for tenant {tenant_id}; skipping")
        return True, existing.data[0], None

    row = {**parsed, "tenant_id": tenant_id, "raw_xml": raw_xml}

    try:
        inserted = supabase.table("dian_xml_documents").insert(row).execute()
    except Exception as exc:
        logger.error(f"DIAN XML insert failed: {exc}")
        return False, None, str(exc)

    return True, inserted.data[0], None
