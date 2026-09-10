# Design: real-data-ingestion-mvp

## D1 — One parser, three doors

All ingestion paths converge on `services/multi_format_parser.py::parse_any_to_siigo_rows()`,
which dispatches on file extension and always returns the **Siigo row shape**:

```python
{"fecha", "referencia_externa", "codigo_cuenta", "descripcion",
 "debito_cents", "credito_cents"}
```

Rows are then rendered back to Siigo CSV text (`_rows_to_csv_text`) and handed to the existing
`ingest_siigo_csv()`.

**Why route through CSV text instead of inserting rows directly?** `ingest_siigo_csv()` already
owns the balance validation and the idempotency key
`(tenant_id, external_reference_id, entry_date)`. Bypassing it to insert rows would have
duplicated both guarantees in a second place. The round-trip is the price of a single
ingestion authority.

**Known cost, accepted:** the round-trip serializes cents to a decimal string and back
(`debito_cents / 100` → CSV → `× 100`). Fine for COP magnitudes; revisit if sub-peso precision
ever matters.

## D2 — DIAN XML is a document, not a journal entry

`parse_dian_ubl_xml()` returns a **single dict** describing a document
(`cufe`, `total_amount_minor`, `tax_amount_minor`, NITs) shaped for the `dian_xml_documents`
table. It does **not** return journal rows.

An earlier implementation returned that dict straight through under a `-> list[dict]`
annotation. Downstream, `_rows_to_csv_text` iterated the dict, received string keys, and raised
`AttributeError`, surfacing to the client as an opaque HTTP 400. Both the plain `.xml` upload
and the PDF-with-embedded-XML path (the DIAN e-invoice case) were affected.

`_ingest_xml_rows()` now derives a balanced entry:

| Account | | Amount |
|---|---|---|
| `1300` Clientes | DEBIT | total (incl. VAT) |
| `4135` Ingresos operacionales | CREDIT | total − VAT |
| `2408` IVA por pagar | CREDIT | VAT (line omitted when zero) |

Credit notes invert every direction. Debits always equal credits, satisfying the ingestion
balance check.

**Guardrails:** a zero payable amount and a VAT exceeding the total both raise rather than
producing a degenerate or unbalanced entry.

**Deliberate omission:** withholding is logged, never posted — see Out of scope in the proposal.

## D3 — Tenant resolution has exactly one authority

Per ARCHITECTURE.md Decision #17, `core/tenant_context.py::resolve_request_tenant_scope()` is
the single resolver for the caller's tenant. Shadow GL endpoints now use it via
`_resolve_tenant_from_scope(user)`:

- Operator (Cliente Cero) → Cliente Cero's tenant
- B2B client → their own tenant
- Authenticated but unresolved → **403**, never a silent fall back to Cliente Cero

The internal endpoints (`/internal/*`) are the exception: they are machine-to-machine and take
`tenant_id` explicitly, because the caller is a poller with no user identity. They are gated by
`INTERNAL_API_KEY` instead, which **fails closed** — an unset key returns 503 for every request
rather than allowing unauthenticated access.

## D4 — Why `/internal/*` sits outside `/api/v1/*`

`vercel.json` rewrites `/api/v1/*` to Railway, so anything mounted there is reachable from the
public internet through `contexia.online`. The poller endpoints are mounted at `/internal/*`,
which no rewrite exposes. Combined with `INTERNAL_API_KEY`, that is defence in depth: not
routed publicly, and authenticated even if it were.

## D5 — Credentials never leave their sovereign boundary

Following ARCHITECTURE.md Decisions #1/#10/#20 (Hermes, GBrain, HubSpot poller all local):

| Secret | Lives in | Never in |
|---|---|---|
| `SIIGO_USERNAME_<tenant>` / `SIIGO_ACCESS_KEY_<tenant>` | Railway env vars + Bitwarden | git, Supabase, local disk |
| `SIIGO_PARTNER_ID` | Railway env var | git (no default value in source) |
| `INTERNAL_API_KEY` | Railway env var + each poller's local `.env` | git |
| Gmail OAuth token / `credentials.json` | Local disk beside the poller | Railway, Vercel, git |
| Supabase service-role key (Gmail poller) | Poller's local `.env` | Railway, git |

Per-tenant Siigo credentials use **dynamic env var names**
(`SIIGO_USERNAME_<TENANT_UUID_WITH_UNDERSCORES>`) rather than a table, so no credential is ever
persisted in the database.

## D6 — `SIIGO_PARTNER_ID` fails closed

Siigo requires a registered `Partner-Id` header. Two different unverified values were in
circulation (`contexiaFinancialOS` in the plan, `contexia-financial-os` in the first
implementation) with **no source for either** — nothing in the repo documents the real one.

Rather than ship a guess, the value is configuration with an empty default; `_partner_id()`
raises `SiigoConfigurationError` when unset. A wrong id would fail at Siigo as an opaque 401;
this converts that into an explicit, actionable error and lets the founder set the correct
value without a code change. A regression test asserts neither guess reappears in source.

## D7 — Poller failure semantics

**Siigo poller (nightly, 02:00):** journals and invoices are fetched independently; one failing
does not abort the other. Errors accumulate into the response rather than raising, so a partial
sync still ingests what it retrieved.

**Gmail poller (every 15 min):** a message is labeled `contexia-processed` **only when every one
of its attachments ingested successfully**. A partial failure leaves it unlabeled so the next
tick retries it. Mail from a sender absent from `gmail_sender_map` is skipped and left unlabeled
— it becomes ingestible the moment the mapping is added, with no manual replay.

Both pollers are **inert without configuration**: missing `INTERNAL_API_KEY` (or Supabase
credentials, for Gmail) logs an error and exits without side effects.

## D8 — Tests must not mock the boundary they verify

Two bugs (D2, and an import of a `services.llm_engine.call_llm` that never existed) shipped to
production **because the tests patched the exact functions under test**. Compounding it, the
inline DIAN XML fixture was invalid — it used `<cbc:CUFE>` where the parser reads `<cbc:UUID>`,
declared no namespaces, and omitted required fields — so it could never have parsed. The mock
was not carelessness; it was load-bearing for a fixture that did not work.

Standing rule for this change: **the LLM is patched at the provider boundary
(`agents.llm_engine.get_ai_response`), never at the wrapper**, and XML tests use the real repo
fixture (`tests/fixtures/dian_invoice_sample.xml`). A test asserts the parse → CSV → re-parse
round-trip that reproduces the original production crash.

Related: a `try/except` around router registration in `main.py` swallowed a `NameError` and
silently unregistered both internal routers — the app booted "fine" without them. Treat a logged
exception in that block as a failure, not a warning.
