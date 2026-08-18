## Why

An audit on 2026-08-18 verified the live Shadow GL tables directly against the database — not
against prior "Phase 5 COMPLETE ✅ LIVE" status reports — and found `erp_journal_entries` (73 rows)
and `dian_xml_documents` (4 rows) are **100% synthetic/fixture data**: CSV-fixture uploads, a
single-timestamp SQL seed, and fabricated CUFE values that don't match DIAN's real format. No real
Siigo/DIAN export has ever been ingested. This directly contradicts the tables' role as the
canonical ledger behind Contexia's "Caja Real" flow, live for the ~10 provisioned B2B tenants plus
Cliente Cero (`ARCHITECTURE.md` → "Flujo estrella", Decision #13/#16).

Real data is coming: Siigo is Contexia's existing paid accounting subscription, and the accountant
will export XML DIAN / CSV Siigo manually and upload them through the ingestion endpoints that
already exist. Nothing today distinguishes a real upload from a test/fixture upload once it lands
in the table — so any dashboard or report built on top of Shadow GL risks silently mixing fabricated
invoices (e.g. `AWS-INFRA-20260603-001-CUFE-HASH-...`) with genuine accounting data.

## What Changes

- Add `is_verified_real BOOLEAN NOT NULL DEFAULT false` to `erp_journal_entries` and
  `dian_xml_documents`.
- Backfill all existing rows (73 + 4) to `false` explicitly — none of today's data is real.
- Add an explicit flag to the two existing manual ingestion endpoints
  (`POST /api/v1/shadow-gl/dian-xml/ingest`, `POST /api/v1/shadow-gl/siigo-csv/ingest`) so the admin
  uploading a file marks it `is_verified_real=true` only when it's a genuine Siigo/DIAN export.
  Default stays `false` — fixtures and future tests never contaminate the flag by accident.

**Non-goals:**
- No automated Siigo API integration — uploads stay manual (accountant exports, admin uploads),
  matching how the endpoints already work.
- No deletion of existing synthetic/test rows — they stay, just correctly flagged.
- No changes to RLS policies or `SECURITY DEFINER` functions — that backlog is explicitly parked
  per founder decision (2026-08-18), out of scope here.
- No changes to the synthetic tenants (`SYN-900100XXX`, `TEST-BRIDGE-*`) in `tenants`.

## Capabilities

### New Capabilities
- `shadow-gl-data-integrity`: tracks whether Shadow GL ledger rows are verified-real accounting
  data vs. synthetic/test data, via an explicit, default-false flag set only on confirmed real
  ingestion.

### Modified Capabilities
(none — no existing spec covers Shadow GL ingestion today; this is new ground)

## Impact

- **Database**: new migration adding 2 columns + 2 backfill statements on
  `kpynymwghfwshvcvevxq` (canonical project — see `docs/supabase-mcp-admin.md`).
- **Backend**: `apps/backend/services/shadow_gl_service.py` (`ingest_dian_xml`, `ingest_siigo_csv`),
  `apps/backend/presentation/shadow_gl_endpoints.py` (both ingestion endpoints, request/response
  models).
- **Docs**: `docs/supabase-mcp-admin.md` §3 already documents the current (100% synthetic) state
  and references this change as the fix — keep both in sync.
- **No frontend impact** — nothing in the PWA/Búnker reads this flag yet; it's a data-integrity
  foundation for whatever consumes Shadow GL as "the real ledger" next.
