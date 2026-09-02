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


def _ingest_xml_rows(raw_xml: str) -> list[dict[str, Any]]:
    """Parse a DIAN UBL 2.1 XML document into Shadow GL rows.

    This thin wrapper is a separate function so tests can patch it cleanly.
    The real DIAN XML parsing lives in shadow_gl_service.parse_dian_ubl_xml().
    """
    try:
        from services.shadow_gl_service import parse_dian_ubl_xml
        return parse_dian_ubl_xml(raw_xml)
    except Exception as exc:
        raise ValueError(f"Could not parse DIAN XML: {exc}") from exc


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
        from services.llm_engine import call_llm
        response_text = await call_llm(prompt, max_tokens=2000)
        raw = response_text.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("LLM did not return a list")
        return rows
    except Exception as exc:
        raise ValueError(f"LLM extraction failed: {exc}") from exc
