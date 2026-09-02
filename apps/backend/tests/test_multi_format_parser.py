"""Tests for multi_format_parser — TDD red first, then green."""

import io
import pytest
from unittest.mock import patch, MagicMock

from services.multi_format_parser import parse_any_to_siigo_rows, UnsupportedFormatError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SIIGO_CSV = (
    "Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito\n"
    "2026-01-15,REF-001,1105,Caja principal,1000000,0\n"
    "2026-01-15,REF-001,3105,Capital,0,1000000\n"
)

VALID_EXCEL_ROWS = [
    ["Fecha", "Referencia Externa", "Código de Cuenta", "Descripción", "Débito", "Crédito"],
    ["2026-01-15", "REF-EXCEL-001", "1105", "Caja principal", 1000000, 0],
    ["2026-01-15", "REF-EXCEL-001", "3105", "Capital", 0, 1000000],
]

DIAN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:CUFE>abc123cufe</cbc:CUFE>
  <cbc:IssueDate>2026-01-15</cbc:IssueDate>
  <cac:InvoiceLine>
    <cbc:LineExtensionAmount currencyID="COP">500000</cbc:LineExtensionAmount>
  </cac:InvoiceLine>
</Invoice>"""


def _make_xlsx_bytes(rows: list) -> bytes:
    """Build a minimal xlsx file in memory from a list of rows."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_pdf_with_xml(xml_content: str) -> bytes:
    """Build a minimal PDF with XML embedded as an attachment."""
    import pypdf
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_attachment("invoice.xml", xml_content.encode("utf-8"))
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# CSV tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parse_csv_produces_rows():
    rows = await parse_any_to_siigo_rows("export.csv", VALID_SIIGO_CSV.encode("utf-8"))
    assert len(rows) == 2
    assert rows[0]["referencia_externa"] == "REF-001"
    assert rows[0]["debito_cents"] == 100000000  # 1_000_000 COP → cents


@pytest.mark.asyncio
async def test_parse_csv_case_insensitive_extension():
    rows = await parse_any_to_siigo_rows("EXPORT.CSV", VALID_SIIGO_CSV.encode("utf-8"))
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# Excel tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parse_xlsx_produces_same_shape_as_csv():
    xlsx_bytes = _make_xlsx_bytes(VALID_EXCEL_ROWS)
    rows = await parse_any_to_siigo_rows("libro.xlsx", xlsx_bytes)
    assert len(rows) == 2
    assert rows[0]["referencia_externa"] == "REF-EXCEL-001"
    assert "debito_cents" in rows[0]
    assert "credito_cents" in rows[0]


@pytest.mark.asyncio
async def test_parse_xls_extension_accepted():
    """XLS is an alias for xlsx path (openpyxl reads both via same code path)."""
    xlsx_bytes = _make_xlsx_bytes(VALID_EXCEL_ROWS)
    rows = await parse_any_to_siigo_rows("libro.xls", xlsx_bytes)
    assert len(rows) >= 1


# ---------------------------------------------------------------------------
# PDF tests — electronic invoice with embedded XML
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parse_pdf_with_embedded_dian_xml():
    pdf_bytes = _make_pdf_with_xml(DIAN_XML)
    with patch("services.multi_format_parser._ingest_xml_rows") as mock_ingest:
        mock_ingest.return_value = [{"referencia_externa": "abc123cufe", "debito_cents": 50000000}]
        rows = await parse_any_to_siigo_rows("factura.pdf", pdf_bytes)
    assert len(rows) == 1
    mock_ingest.assert_called_once()


@pytest.mark.asyncio
async def test_parse_pdf_without_xml_calls_llm():
    import pypdf
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    plain_pdf = buf.getvalue()

    with patch("services.multi_format_parser._extract_rows_via_llm") as mock_llm:
        mock_llm.return_value = [{"referencia_externa": "LLM-001", "debito_cents": 10000}]
        rows = await parse_any_to_siigo_rows("factura_manual.pdf", plain_pdf)
    assert len(rows) == 1
    mock_llm.assert_called_once()


# ---------------------------------------------------------------------------
# Unsupported format
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unsupported_format_raises():
    with pytest.raises(UnsupportedFormatError):
        await parse_any_to_siigo_rows("archivo.docx", b"some content")


@pytest.mark.asyncio
async def test_unknown_extension_raises():
    with pytest.raises(UnsupportedFormatError):
        await parse_any_to_siigo_rows("archivo.txt", b"plain text")
