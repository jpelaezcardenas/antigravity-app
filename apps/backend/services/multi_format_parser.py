"""Multi-format parser — converts CSV, XLSX, XML, and PDF files to the Shadow GL row shape.

All public functions produce the same flat list as `parse_siigo_csv()`:
[
    {
        "fecha": "YYYY-MM-DD",
        "referencia_externa": str,
        "codigo_cuenta": str,
        "descripcion": str,
        "debito_cents": int,
        "credito_cents": int,
    },
    ...
]

Entry point: `parse_any_to_siigo_rows(filename, content_bytes)`.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class UnsupportedFormatError(ValueError):
    """Raised when the file extension is not supported by any parser path."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def parse_any_to_siigo_rows(filename: str, content: bytes) -> list[dict[str, Any]]:
    """Dispatch to the correct parser based on file extension.

    Args:
        filename: Original filename (extension used for dispatch).
        content: Raw file bytes.

    Returns:
        Flat list of Shadow GL row dicts (same shape as parse_siigo_csv()).

    Raises:
        UnsupportedFormatError: if the extension is not supported.
        SiigoCsvParseError / ValueError: if the file content is malformed.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".csv":
        return _parse_csv_bytes(content)
    if ext in (".xml",):
        return _parse_xml_bytes(content)
    if ext in (".xlsx", ".xls"):
        return _parse_excel_bytes(content)
    if ext == ".pdf":
        return await _parse_pdf_bytes(content)

    raise UnsupportedFormatError(
        f"File format '{ext}' is not supported. Accepted: .csv, .xml, .xlsx, .xls, .pdf"
    )


# ---------------------------------------------------------------------------
# CSV path — delegates to the existing parser
# ---------------------------------------------------------------------------

def _parse_csv_bytes(content: bytes) -> list[dict[str, Any]]:
    from services.shadow_gl_service import parse_siigo_csv

    csv_text = content.decode("utf-8", errors="replace")
    return parse_siigo_csv(csv_text)


# ---------------------------------------------------------------------------
# XML path — delegates to the existing DIAN UBL parser
# ---------------------------------------------------------------------------

def _parse_xml_bytes(content: bytes) -> list[dict[str, Any]]:
    raw_xml = content.decode("utf-8", errors="replace")
    return _ingest_xml_rows(raw_xml)


# Colombian PUC accounts used when deriving a journal entry from a DIAN document.
# These are the same codes siigo_api_client._invoice_to_rows() uses, kept in sync
# deliberately so both ingestion paths produce comparable entries.
_PUC_RECEIVABLE = "1300"  # Clientes (accounts receivable)
_PUC_REVENUE = "4135"     # Ingresos operacionales (commerce)
_PUC_VAT_PAYABLE = "2408"  # IVA por pagar


def _ingest_xml_rows(raw_xml: str) -> list[dict[str, Any]]:
    """Parse a DIAN UBL 2.1 XML document into balanced Shadow GL rows.

    parse_dian_ubl_xml() returns a SINGLE document dict shaped for the
    `dian_xml_documents` table (cufe, totals, NITs) — NOT journal rows. This
    function derives the double-entry rows the Shadow GL ingestion expects.

    An invoice/debit note produces:
        DEBIT  1300 Clientes        = total (incl. VAT)
        CREDIT 4135 Ingresos        = total - VAT
        CREDIT 2408 IVA por pagar   = VAT            (omitted when VAT is 0)

    A credit note reverses those directions. Debits always equal credits, which
    the downstream ingest_siigo_csv() balance check requires.
    """
    try:
        from services.shadow_gl_service import parse_dian_ubl_xml
        doc = parse_dian_ubl_xml(raw_xml)
    except Exception as exc:
        raise ValueError(f"Could not parse DIAN XML: {exc}") from exc

    total = int(doc.get("total_amount_minor") or 0)
    if total == 0:
        raise ValueError("DIAN document has a zero payable amount — nothing to ingest")

    vat = int(doc.get("tax_amount_minor") or 0)
    if vat > total:
        raise ValueError(
            f"DIAN document VAT ({vat}) exceeds its payable amount ({total}) — refusing to "
            "derive an unbalanced entry"
        )
    net = total - vat

    # Withholding is parsed by parse_dian_ubl_xml but deliberately NOT posted here:
    # its correct treatment (retefuente/reteIVA/reteICA accounts) is an accounting
    # decision this parser must not invent. Log it so the omission is visible rather
    # than silent — see the OpenSpec change before adding withholding lines.
    withholding = int(doc.get("withholding_amount_minor") or 0)
    if withholding:
        logger.warning(
            "DIAN document %s carries withholding of %d minor units, which is NOT posted to "
            "the Shadow GL. The derived entry reflects the gross amount only.",
            doc.get("cufe"),
            withholding,
        )

    cufe = str(doc.get("cufe") or "")
    fecha = str(doc.get("issue_date") or "")
    doc_type = str(doc.get("document_type") or "invoice")
    reference = f"DIAN-{cufe}"
    description = f"{doc_type} {cufe} (NIT {doc.get('issuer_nit', '')})"

    # A credit note reverses the flow of an invoice/debit note.
    reversed_flow = doc_type == "credit_note"

    def _row(account: str, amount: int, is_debit: bool) -> dict[str, Any]:
        debit_side = is_debit if not reversed_flow else not is_debit
        return {
            "fecha": fecha,
            "referencia_externa": reference,
            "codigo_cuenta": account,
            "descripcion": description,
            "debito_cents": amount if debit_side else 0,
            "credito_cents": 0 if debit_side else amount,
        }

    rows = [
        _row(_PUC_RECEIVABLE, total, is_debit=True),
        _row(_PUC_REVENUE, net, is_debit=False),
    ]
    if vat:
        rows.append(_row(_PUC_VAT_PAYABLE, vat, is_debit=False))

    return rows


# ---------------------------------------------------------------------------
# Excel path — openpyxl
# ---------------------------------------------------------------------------

def _parse_excel_bytes(content: bytes) -> list[dict[str, Any]]:
    """Parse an Excel file (.xlsx / .xls) with Siigo-compatible column headers.

    Expected columns (same as Siigo CSV export):
    Fecha, Referencia Externa, Código de Cuenta, Descripción, Débito, Crédito
    """
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)

    try:
        raw_headers = next(rows_iter)
    except StopIteration:
        raise ValueError("Excel file is empty")

    headers = [str(h).strip() if h is not None else "" for h in raw_headers]
    headers_lower = [h.lower() for h in headers]

    required = {"fecha", "referencia externa", "código de cuenta", "descripción"}
    missing = required - set(headers_lower)
    if missing:
        raise ValueError(f"Excel missing required columns: {', '.join(sorted(missing))}")

    # Build a column-index lookup
    idx: dict[str, int] = {name: i for i, name in enumerate(headers_lower)}

    def _col(row: tuple, name: str, default: Any = "") -> Any:
        i = idx.get(name)
        return row[i] if i is not None and i < len(row) else default

    def _cents(val: Any) -> int:
        if val is None or val == "":
            return 0
        try:
            return round(float(str(val).replace(",", "").strip()) * 100)
        except (ValueError, TypeError):
            return 0

    result: list[dict[str, Any]] = []
    for row in rows_iter:
        if all(c is None for c in row):
            continue
        fecha_raw = _col(row, "fecha")
        fecha = str(fecha_raw).strip() if fecha_raw else ""
        if hasattr(fecha_raw, "date"):
            fecha = fecha_raw.date().isoformat()

        result.append(
            {
                "fecha": fecha,
                "referencia_externa": str(_col(row, "referencia externa", "")).strip(),
                "codigo_cuenta": str(_col(row, "código de cuenta", "")).strip(),
                "descripcion": str(_col(row, "descripción", "")).strip(),
                "debito_cents": _cents(_col(row, "débito", 0)),
                "credito_cents": _cents(_col(row, "crédito", 0)),
            }
        )

    wb.close()
    return result


# ---------------------------------------------------------------------------
# PDF path — tries embedded XML attachment first, then LLM fallback
# ---------------------------------------------------------------------------

async def _parse_pdf_bytes(content: bytes) -> list[dict[str, Any]]:
    """Parse a PDF, preferring an embedded DIAN XML attachment over LLM extraction."""
    try:
        xml_rows = _extract_xml_from_pdf(content)
        if xml_rows is not None:
            return xml_rows
    except Exception as exc:
        logger.warning(f"PDF XML extraction failed, falling back to LLM: {exc}")

    return await _extract_rows_via_llm(content)


def _extract_xml_from_pdf(content: bytes) -> list[dict[str, Any]] | None:
    """Extract and parse an embedded DIAN XML attachment from a PDF.

    Returns None if no XML attachment is found.
    """
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(content))
    embedded = getattr(reader, "attachments", {})

    for name, data_list in embedded.items():
        name_lower = name.lower()
        if name_lower.endswith(".xml"):
            for data in data_list:
                try:
                    raw_xml = data.decode("utf-8", errors="replace")
                    rows = _ingest_xml_rows(raw_xml)
                    if rows:
                        logger.info(f"Extracted {len(rows)} rows from PDF attachment '{name}'")
                        return rows
                except Exception as exc:
                    logger.warning(f"Could not parse PDF attachment '{name}': {exc}")

    return None


async def _extract_rows_via_llm(content: bytes) -> list[dict[str, Any]]:
    """Extract Shadow GL rows from a plain-text PDF using the LLM engine.

    This is a best-effort path for non-electronic invoices (image/text PDFs).
    The LLM is asked to produce a JSON array matching the Shadow GL row shape.
    """
    import json
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if not text:
        raise ValueError("PDF contains no extractable text — consider uploading an electronic invoice XML instead")

    prompt = (
        "You are a Colombian accounting assistant. Extract all journal entries from the following "
        "invoice document and return them as a JSON array. Each element must have exactly these fields: "
        "fecha (YYYY-MM-DD), referencia_externa (string), codigo_cuenta (Colombian PUC code), "
        "descripcion (string), debito_cents (integer, COP amount × 100), credito_cents (integer, COP amount × 100). "
        "Return ONLY the JSON array, no explanation.\n\n"
        f"DOCUMENT:\n{text[:4000]}"
    )

    try:
        # The LLM entry point lives in agents.llm_engine (NOT services.llm_engine, which
        # does not exist) and get_ai_response is SYNCHRONOUS — run it off the event loop
        # so a slow provider cannot block the whole backend.
        import asyncio
        from agents.llm_engine import get_ai_response

        response_text = await asyncio.to_thread(
            get_ai_response,
            prompt=prompt,
            max_tokens=2000,
            temperature=0.0,  # deterministic extraction, not creative writing
        )
        if isinstance(response_text, dict):
            # response_format defaults to "text", but guard anyway: a dict here means
            # the engine already parsed JSON for us.
            rows = response_text.get("rows", response_text)
        else:
            raw = str(response_text).strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            rows = json.loads(raw)

        if not isinstance(rows, list):
            raise ValueError("LLM did not return a list of rows")
        return rows
    except Exception as exc:
        raise ValueError(f"LLM extraction failed: {exc}") from exc
