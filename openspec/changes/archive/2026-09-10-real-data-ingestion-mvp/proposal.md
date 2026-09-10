# Proposal: real-data-ingestion-mvp

**Status:** apply (deployed, pending Stage 11 close-out)
**Created:** 2026-09-01
**Owner:** Juan David (founder)

## Why

Contexia's first paying B2B clients see Pulso Diario, Centinela and Radar rendered from
**synthetic seed data**. The product promise ("your real cash, today") is not met until
their own accounting data reaches the Shadow GL.

The Shadow GL itself already existed in production with working ingestion functions
(`ingest_siigo_csv`, `ingest_dian_xml`). Three things blocked clients from actually using it:

1. **A tenant-isolation bug.** `shadow_gl_endpoints.py` resolved the target tenant by
   querying `is_cliente_cero=true` — hardcoded. Any client uploading a CSV would have had
   their financial data written into **Cliente Cero's** ledger, not their own. The three
   POST endpoints also carried no `Depends(get_current_user)`, so they were reachable
   unauthenticated. This is a data-segregation defect, not a missing feature.
2. **No path from a client to the endpoint.** Ingestion was curl-only. No UI, no automation.
3. **Only CSV and DIAN XML were parseable.** Clients hold Excel exports and PDF invoices.

## What changes

Four tracks, one shared parser:

| Track | Delivers |
|---|---|
| **Prerequisite 0** | JWT-based tenant resolution on all Shadow GL POST endpoints |
| **Track 4** | `multi_format_parser.py` — one entry point for CSV / XLSX / XML / PDF |
| **Track 1** | Self-service upload card in the PWA (`/app/overview`) |
| **Track 2** | Siigo REST API nightly sync per tenant |
| **Track 3** | Gmail attachment ingestion from Taty's inbox every 15 min |

Tracks 1, 2 and 3 are three different *doors* into the same room: each resolves a tenant,
parses a file, and calls the existing idempotent `ingest_siigo_csv()`. Track 4 is the shared
library all three depend on.

## Deviation from the original plan (deliberate)

The plan proposed **three separate OpenSpec changes** (`pwa-data-upload-self-service`,
`siigo-api-live-sync`, `gmail-adjuntos-ingest`) to be run in parallel. This is **one change**
instead, because:

- The repo's own invariant is *one active change at a time* — `init.sh` hard-gates it and
  `HARNESS.md` describes `feature_list.json` as a pointer enforcing exactly that. Three
  simultaneous changes would violate the harness rule the plan sits inside.
- All three tracks depend on Track 4, which is not separable. Splitting would have produced
  three changes each blocked on the same unshipped library.
- The tenant-isolation fix (Prerequisite 0) is a precondition for all three; it belongs to
  none of them individually.

The tradeoff accepted: this change is larger than the repo norm. It is justified by the
shared dependency, not by convenience, and the task list keeps the tracks separable.

## Out of scope

- **Withholding tax (retenciones) accounting.** `parse_dian_ubl_xml` extracts a withholding
  amount; deriving `retefuente`/`reteIVA`/`reteICA` postings from it is an accounting decision
  requiring a licensed accountant, not a parser default. The derived entry currently posts the
  gross amount and logs a warning when withholding is present.
- **Live Wompi/payment linkage**, Radar model changes, and any PWA screen beyond the upload
  card.
- **Backfill of historical data** for existing tenants.

## Risks

| Risk | Mitigation |
|---|---|
| Client data written to the wrong tenant | Prerequisite 0; `resolve_request_tenant_scope` is the single resolver, 403 when unresolved |
| Siigo credentials leaking into the repo | Credentials only ever in Railway env vars + Bitwarden; dynamic env var names, never in DB or source |
| Siigo Partner-Id guessed wrong | `SIIGO_PARTNER_ID` fails closed (empty default raises `SiigoConfigurationError`) rather than authenticating with a guess |
| Derived DIAN entries unbalanced | Parser asserts debits == credits; ingestion rejects imbalanced batches |
| Gmail poller re-ingesting the same email | Message labeled `contexia-processed` only when every attachment succeeded; `ingest_siigo_csv` is idempotent on `(tenant_id, external_reference_id, entry_date)` |
| Autonomous writes to client ledgers | Sync is **read-only against Siigo/Gmail**; nothing is ever written back to a client's ERP or inbox |
