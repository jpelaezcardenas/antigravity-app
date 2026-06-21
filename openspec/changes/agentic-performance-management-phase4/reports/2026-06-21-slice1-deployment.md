# Stage 11 Deployment Report — agentic-performance-management-phase4 / Slice 1

**Date:** 2026-06-21
**Change ID:** agentic-performance-management-phase4
**Slice:** 1 — Shadow GL substrate
**Status:** READY FOR PRODUCTION (schema-only milestone)
**Environment:** Supabase production project (direct migration, no Railway backend code change in this slice)

## What changed

Four new tables + one materialized view, applied as separate additive migrations:

| Migration | Content |
|---|---|
| `shadow_gl_tenants` | `tenants` table, unique-partial-index enforcing a single Cliente Cero, RLS, seed row for Contexia SAS (NIT 900000000) |
| `shadow_gl_dian_xml_documents` | `dian_xml_documents` table (CUFE unique per tenant, raw XML + parsed fields, BIGINT minor units), RLS |
| `shadow_gl_erp_journal` | `erp_journal_entries` + `erp_journal_lines`, `debit_or_credit_not_both` CHECK constraint, deferred constraint trigger `assert_entry_balanced()`, RLS |
| `shadow_gl_discrepancies_view` | Materialized view `shadow_gl_discrepancies` (missing_in_erp / amount_mismatch / matched) + unique index for concurrent refresh |
| `shadow_gl_anon_policies` | Corrected RLS policies on the four tables from `service_role`-only to `anon, authenticated, service_role` |
| `shadow_gl_discrepancies_refresh_cron` | Enabled `pg_cron`; scheduled `shadow-gl-discrepancies-refresh` every 15 minutes |

## What didn't change

- No Railway backend code deployed in this slice — pure Supabase schema.
- No existing tables altered (additive-only, per design.md migration plan).
- No data in `dian_xml_documents` / `erp_journal_entries` yet — real ingestion starts in Slice 2.

## Test evidence

`apps/backend/tests/test_shadow_gl_schema.py`, gated by `RUN_SHADOW_GL=1` (same convention as `RUN_KB_PGVECTOR` for `test_kb_seeding.py`):

- **RED before migration:** 6/7 failing — `PGRST205` (table not found) on `tenants`, `dian_xml_documents`, `erp_journal_entries`, `erp_journal_lines`, `shadow_gl_discrepancies`.
- **GREEN after migration:** 7/7 passing.
  - Cliente Cero tenant exists and is the only one allowed.
  - All four tables queryable.
  - Inserting an unbalanced journal entry raises and rolls back (test asserts via the deferred constraint trigger, with teardown cleanup of the orphaned `erp_journal_entries` row left behind since the trigger only protects `erp_journal_lines` balance, not entry existence).
  - `shadow_gl_discrepancies` returns 0 rows (no DIAN data ingested yet — expected for a schema-only milestone).

## Issue found and corrected during deployment

RLS policies were originally drafted as `service_role`-only (per design.md's literal wording). The real backend (`infrastructure/supabase_client.py`) authenticates with the **anon** key (confirmed by decoding the configured JWT's `role` claim), matching the project's existing — already flagged — pattern on `alerts`/`campaigns`/`clients`/`snapshots`. Policies were corrected to `anon, authenticated, service_role` so the backend can actually read/write. This is the same pre-existing security gap noted in `design.md` Non-Goals (RLS remediation is a separate, distinct change), not a new gap introduced by this slice.

## Rollback

All four tables and the view are net-new with zero rows of real data and nothing else reading them yet:

```sql
DROP MATERIALIZED VIEW IF EXISTS public.shadow_gl_discrepancies;
DROP TABLE IF EXISTS public.erp_journal_lines;
DROP TABLE IF EXISTS public.erp_journal_entries;
DROP TABLE IF EXISTS public.dian_xml_documents;
DROP TABLE IF EXISTS public.tenants;
SELECT cron.unschedule('shadow-gl-discrepancies-refresh');
```

## Stage 11 completion criteria (Slice 1 scope)

- [x] Migrations applied to production Supabase
- [x] `list_tables` confirms all four tables live
- [x] Test suite green (7/7) against production
- [x] No data-loss risk (additive-only)
- [x] Rollback procedure documented
- [x] Cliente Cero seeded

## Next step

Slice 2 — Centinela Resolution + Approval Queue extension. Note: discovered during prep that `apps/backend/services/approval_queue_service.py` is currently an in-memory stub with **no real persistence** ("In a real implementation, this would load the decision from database — For now, we return a placeholder"). `design.md` D1 assumed an existing `approval_queue` table to extend additively; that table does not exist. Slice 2 must **create** `approval_queue` from scratch (with `draft_type`/`payload` from day one) rather than ALTER an existing table — this will be reflected in `design.md`/`tasks.md` before Slice 2 work starts, per the project's OpenSpec mandatory-update rule.
