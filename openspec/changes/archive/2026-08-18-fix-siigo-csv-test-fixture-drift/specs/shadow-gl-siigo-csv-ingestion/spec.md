## ADDED Requirements

### Requirement: Siigo CSV parser accepts Spanish export headers and returns flat rows
`parse_siigo_csv()` SHALL require the Spanish Siigo export column headers `fecha`,
`referencia externa`, `código de cuenta`, `descripción` (required) and `débito`, `crédito`
(optional, blank treated as zero), matched case-insensitively. It SHALL return a flat list of
row dicts — one dict per CSV line, each with `fecha`, `referencia_externa`, `codigo_cuenta`,
`descripcion`, `debito_cents`, `credito_cents` — not grouped by transaction.

#### Scenario: Valid Siigo CSV parses to flat rows
- **WHEN** a CSV with the required Spanish headers is passed to `parse_siigo_csv`
- **THEN** the function returns a list with one dict per data row, each containing
  `fecha`/`referencia_externa`/`codigo_cuenta`/`descripcion`/`debito_cents`/`credito_cents`

#### Scenario: Missing required column is rejected
- **WHEN** a CSV is missing one of `fecha`, `referencia externa`, `código de cuenta`, or
  `descripción`
- **THEN** `parse_siigo_csv` raises `SiigoCsvParseError` naming the missing column(s)

#### Scenario: Monetary amounts convert to integer cents
- **WHEN** a row has a `débito` or `crédito` value like `"850000.00"`
- **THEN** the corresponding `debito_cents`/`credito_cents` field is the integer minor-units value
  (`85000000`)

#### Scenario: Blank debit/credit treated as zero
- **WHEN** a row's `débito` or `crédito` cell is empty
- **THEN** the corresponding `*_cents` field is `0`, not an error

#### Scenario: Invalid date format is rejected
- **WHEN** a row's `fecha` is not ISO 8601 (`YYYY-MM-DD`)
- **THEN** `parse_siigo_csv` raises `SiigoCsvParseError` naming the row and the bad value

#### Scenario: Non-numeric monetary value is rejected
- **WHEN** a row's `débito` or `crédito` cannot be parsed as a decimal amount
- **THEN** `parse_siigo_csv` raises `SiigoCsvParseError`

#### Scenario: Negative amounts are rejected
- **WHEN** a row's computed `debito_cents` or `credito_cents` would be negative
- **THEN** `parse_siigo_csv` raises `SiigoCsvParseError`

#### Scenario: Empty CSV body returns an empty list
- **WHEN** a CSV has only the header row and no data rows
- **THEN** `parse_siigo_csv` returns `[]` without raising

### Requirement: Parser rejects a batch where total debits do not equal total credits
`parse_siigo_csv()` SHALL sum `debito_cents` and `credito_cents` across all parsed rows and raise
`SiigoCsvParseError` if the batch total debits do not equal total credits.

#### Scenario: Imbalanced batch is rejected at parse time
- **WHEN** a CSV's rows sum to unequal total debits and credits
- **THEN** `parse_siigo_csv` raises `SiigoCsvParseError` reporting both totals

### Requirement: Ingestion groups parsed rows into journal entries by transaction reference
`ingest_siigo_csv()` SHALL group `parse_siigo_csv`'s flat rows into one `erp_journal_entries` row
per distinct `referencia_externa`, with each row's line-level detail (`codigo_cuenta`,
`debito_cents`, `credito_cents`, `descripcion`) inserted as a corresponding `erp_journal_lines`
row linked to that entry.

#### Scenario: Multiple lines with the same reference group into one entry
- **WHEN** a CSV contains two or more rows sharing the same `referencia_externa`
- **THEN** `ingest_siigo_csv` creates exactly one `erp_journal_entries` row for that reference,
  with one `erp_journal_lines` row per underlying CSV row
