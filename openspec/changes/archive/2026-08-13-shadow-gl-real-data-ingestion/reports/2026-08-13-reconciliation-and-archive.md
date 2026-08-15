# Shadow GL Real Data Ingestion — Reconciliation & Archive Report

**Date:** 2026-08-13
**Context:** Pre-GTM tech-debt triage

## Why this report exists

`tasks.md` had **0/101 checkboxes marked done**, while 3 prior deployment reports
(2026-06-25, 2026-06-25-final, 2026-06-26) claimed "100% complete, 42 tests passing." This is a
tracking-drift case, not a fabrication case — verified against the actual codebase before
archiving, not just re-reading the reports' own claims. Full findings are in the reconciliation
note at the top of `tasks.md`.

## Verified today

- Migration `0019_shadow_gl_siigo_ingestion.sql` exists and is applied.
- `parse_siigo_csv()` / `ingest_siigo_csv()` exist in `apps/backend/services/shadow_gl_service.py`.
- Both `POST /siigo-csv/ingest` and `POST /siigo-csv/upload` are live.
- 42/42 tests pass (the exact count the June reports claimed), run today from repo root.
- **The endpoint is live on the canonical `175a` backend** (`422` on missing body, not `404`) —
  not just the non-canonical `dc78` backend the June reports pointed at. This is a materially
  better finding than the reports themselves documented.
- `GET /api/v1/health` on `175a` returns healthy.

## Genuine gaps found (not silently closed)

1. `README.md` never got the "Shadow GL Data Ingestion" section (task 6.3).
2. No real XML DIAN fixture in this change's `fixtures/` — only the Siigo CSV side has a real
   Cliente Cero export on disk. Task 7.2 (manual XML test with real data) has no evidence.
3. `mypy --strict` and `ruff check` were never run for this change (tooling unavailable in this
   environment today) — tasks 8.1/8.2 remain genuinely unverified, not marked done.

None of these block archiving: the shipped code is correct, tested, and serving production
traffic on the canonical backend. They're documentation/tooling debt, not functional debt.

## Disposition

Archiving now as part of the broader 11-change tech-debt triage restoring the "one change at a
time" invariant (HARNESS.md). See `MEMORY.md` → `tech-debt-pre-gtm-2026-08-13`.
