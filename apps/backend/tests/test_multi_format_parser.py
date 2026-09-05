"""Tests for multi_format_parser — TDD red first, then green."""

import io
from pathlib import Path

import pytest
from unittest.mock import patch

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

# The REAL DIAN fixture already used by test_shadow_gl_integration.py. An earlier
# inline fixture here was invalid (it used <cbc:CUFE> where the parser reads
# <cbc:UUID>, declared no cbc/cac namespaces, and omitted the required NIT and
# LegalMonetaryTotal fields) — it could never have parsed, which is precisely why
# the XML tests used to mock the parser away and missed a real bug.
DIAN_XML = (Path(__file__).parent / "fixtures" / "dian_invoice_sample.xml").read_text(
    encoding="utf-8"
)

# Known values of that fixture: payable 119_000.00 COP, VAT 19_000.00 COP.
DIAN_TOTAL_CENTS = 11_900_000
DIAN_VAT_CENTS = 1_900_000
DIAN_NET_CENTS = DIAN_TOTAL_CENTS - DIAN_VAT_CENTS
DIAN_CUFE = "test-cufe-0001-synthetic-fixture"


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
async def test_parse_pdf_with_embedded_dian_xml_extracts_real_cufe():
    """The PDF path must really parse the embedded XML — no mock of the boundary.

    Regression guard: this previously patched _ingest_xml_rows, so it asserted the
    mock's own return value and never noticed that the real function returned a
    document dict instead of journal rows.
    """
    pdf_bytes = _make_pdf_with_xml(DIAN_XML)
    rows = await parse_any_to_siigo_rows("factura.pdf", pdf_bytes)

    assert isinstance(rows, list), "must return journal ROWS, not a document dict"
    assert all(isinstance(r, dict) for r in rows)
    # The CUFE is genuinely extracted from the XML, not supplied by a mock.
    assert all(DIAN_CUFE in r["referencia_externa"] for r in rows)


@pytest.mark.asyncio
async def test_parse_pdf_without_xml_uses_llm_engine():
    """A text PDF with no embedded XML must reach the real LLM entry point.

    The LLM call itself is patched at agents.llm_engine.get_ai_response — i.e. at the
    provider boundary, NOT at _extract_rows_via_llm. That way the import path and the
    call signature are actually exercised; patching the wrapper hid a broken import
    of a module (services.llm_engine) and a function (call_llm) that never existed.
    """
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    plain_pdf = buf.getvalue()

    llm_reply = (
        '[{"fecha": "2026-01-15", "referencia_externa": "LLM-001", '
        '"codigo_cuenta": "5105", "descripcion": "Servicios", '
        '"debito_cents": 10000, "credito_cents": 0}]'
    )

    with patch("agents.llm_engine.get_ai_response", return_value=llm_reply) as mock_llm:
        # A blank page extracts no text, so the parser raises before reaching the LLM.
        # That is correct behavior — assert it explicitly instead of pretending otherwise.
        with pytest.raises(Exception) as exc_info:
            await parse_any_to_siigo_rows("factura_manual.pdf", plain_pdf)

    assert "no extractable text" in str(exc_info.value).lower()
    mock_llm.assert_not_called()


@pytest.mark.asyncio
async def test_parse_plain_xml_produces_balanced_rows():
    """Uploading a .xml file directly must produce balanced double-entry rows.

    There was NO test for this path at all; it returned a dict and crashed downstream
    in _rows_to_csv_text, surfacing to the client as a generic HTTP 400.
    """
    rows = await parse_any_to_siigo_rows("factura.xml", DIAN_XML.encode("utf-8"))

    assert isinstance(rows, list) and len(rows) == 3

    total_debits = sum(r["debito_cents"] for r in rows)
    total_credits = sum(r["credito_cents"] for r in rows)
    assert total_debits == total_credits, "derived entry must balance"
    assert total_debits == DIAN_TOTAL_CENTS

    by_account = {r["codigo_cuenta"]: r for r in rows}
    assert by_account["1300"]["debito_cents"] == DIAN_TOTAL_CENTS
    assert by_account["4135"]["credito_cents"] == DIAN_NET_CENTS
    assert by_account["2408"]["credito_cents"] == DIAN_VAT_CENTS


@pytest.mark.asyncio
async def test_xml_rows_survive_the_csv_roundtrip():
    """End-to-end guard for the exact crash that reached production.

    parse_any_to_siigo_rows() output is fed to _rows_to_csv_text() by the upload
    endpoint, and that combination raised AttributeError on the XML path.
    """
    from presentation.shadow_gl_endpoints import _rows_to_csv_text

    rows = await parse_any_to_siigo_rows("factura.xml", DIAN_XML.encode("utf-8"))
    csv_text = _rows_to_csv_text(rows)

    assert "Fecha,Referencia Externa" in csv_text
    assert DIAN_CUFE in csv_text

    # And the CSV must parse back into the same balanced entry.
    from services.shadow_gl_service import parse_siigo_csv

    reparsed = parse_siigo_csv(csv_text)
    assert sum(r["debito_cents"] for r in reparsed) == DIAN_TOTAL_CENTS
    assert sum(r["credito_cents"] for r in reparsed) == DIAN_TOTAL_CENTS


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
