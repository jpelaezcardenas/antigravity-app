### Requirement: A single parser entry point accepts every supported client file format

`services/multi_format_parser.py::parse_any_to_siigo_rows(filename, content)` SHALL dispatch on
the file extension (case-insensitively) and SHALL always return a flat list of Siigo-shaped row
dicts — `fecha`, `referencia_externa`, `codigo_cuenta`, `descripcion`, `debito_cents`,
`credito_cents` — regardless of the input format. It SHALL raise `UnsupportedFormatError` for any
extension it does not handle.

#### Scenario: Siigo CSV parses to rows
- **WHEN** a `.csv` file with Siigo export headers is passed
- **THEN** the function delegates to `parse_siigo_csv()` and returns its rows

#### Scenario: Extension matching is case-insensitive
- **WHEN** a file named `EXPORT.CSV` is passed
- **THEN** it is parsed as CSV, not rejected

#### Scenario: Excel workbook produces the same row shape as CSV
- **WHEN** an `.xlsx` or `.xls` file with the Spanish Siigo column headers is passed
- **THEN** the returned rows carry the same six keys, with monetary values as integer cents

#### Scenario: Unsupported extension is rejected explicitly
- **WHEN** a file with an extension outside `{.csv, .xlsx, .xls, .xml, .pdf}` is passed
- **THEN** `UnsupportedFormatError` is raised naming the unsupported format

---

### Requirement: A DIAN UBL 2.1 document is converted into a balanced journal entry

`parse_dian_ubl_xml()` returns a single document dict shaped for the `dian_xml_documents` table,
NOT journal rows. `_ingest_xml_rows()` SHALL derive double-entry rows from it such that total
debits equal total credits, so the downstream `ingest_siigo_csv()` balance check passes.

An invoice or debit note SHALL post: DEBIT `1300` (Clientes) for the payable total, CREDIT `4135`
(Ingresos operacionales) for total minus VAT, and CREDIT `2408` (IVA por pagar) for the VAT. A
credit note SHALL invert every direction.

#### Scenario: Plain XML upload produces balanced rows
- **WHEN** a valid DIAN UBL 2.1 invoice XML is passed to `parse_any_to_siigo_rows`
- **THEN** a list of rows is returned whose summed `debito_cents` equals summed `credito_cents`,
  and equals the document's payable amount in minor units

#### Scenario: VAT line is omitted when the document carries no VAT
- **WHEN** the document's tax amount is zero or absent
- **THEN** only the `1300` and `4135` rows are produced, still balanced

#### Scenario: Credit note reverses the entry direction
- **WHEN** the parsed `document_type` is `credit_note`
- **THEN** the `1300` row is a credit and the `4135`/`2408` rows are debits

#### Scenario: The CUFE identifies the entry
- **WHEN** rows are derived from a DIAN document
- **THEN** every row's `referencia_externa` contains the document's CUFE, so re-ingesting the
  same document is idempotent on `(tenant_id, external_reference_id, entry_date)`

#### Scenario: Zero payable amount is rejected
- **WHEN** the document's payable amount is zero
- **THEN** a `ValueError` is raised rather than emitting a degenerate entry

#### Scenario: VAT exceeding the total is rejected
- **WHEN** the parsed VAT is greater than the payable total
- **THEN** a `ValueError` is raised rather than emitting an unbalanced entry

#### Scenario: Withholding is surfaced, never silently posted
- **WHEN** the document carries a withholding amount
- **THEN** the derived entry posts the gross amount and a warning naming the CUFE and the
  withholding amount is logged

---

### Requirement: PDF invoices are parsed via embedded XML first, LLM second

For a `.pdf` file, the parser SHALL first attempt to extract an embedded XML attachment (the DIAN
electronic-invoice case) and parse it as a DIAN document. Only when no XML attachment is present
SHALL it fall back to extracting text and asking the LLM engine to structure it.

The LLM entry point is `agents.llm_engine.get_ai_response`, which is synchronous and SHALL be
invoked off the event loop.

#### Scenario: Electronic invoice PDF uses its embedded XML
- **WHEN** a PDF containing an `.xml` attachment is passed
- **THEN** the XML is parsed and the resulting rows carry the CUFE genuinely extracted from it

#### Scenario: PDF with no extractable text fails with a clear message
- **WHEN** a PDF has neither an XML attachment nor extractable text
- **THEN** an error is raised stating that no text could be extracted and suggesting the XML
  route, and the LLM is NOT called

---

### Requirement: Ingestion tests SHALL NOT mock the boundary under verification

Tests covering the XML and LLM paths SHALL exercise the real parsing code. The LLM SHALL be
patched only at the provider boundary (`agents.llm_engine.get_ai_response`), never at
`_extract_rows_via_llm`. XML tests SHALL use the real repository fixture
`tests/fixtures/dian_invoice_sample.xml`, never an inline fixture that the parser cannot parse.

#### Scenario: The parse-to-CSV round-trip is covered
- **WHEN** rows derived from a DIAN XML are passed to `_rows_to_csv_text()` and re-parsed with
  `parse_siigo_csv()`
- **THEN** the entry still balances and still totals the document's payable amount
