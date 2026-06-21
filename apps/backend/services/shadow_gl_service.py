"""
Shadow GL Service

Parses DIAN UBL 2.1 XML documents (invoices, credit notes, debit notes) and
ingests them into `dian_xml_documents`. Ingestion is currently triggered by
manual upload (POST /api/v1/shadow-gl/dian-xml/ingest); a live DIAN webhook
is a later, additive trigger onto the same parser (see design.md Slice 2
decision, 2026-06-21).
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple

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
