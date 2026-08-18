## Context

Shadow GL ingestion has three live call sites that insert into `erp_journal_entries` /
`erp_journal_lines` / `dian_xml_documents`, all funneling through two service functions:

- `POST /api/v1/shadow-gl/dian-xml/ingest` → `ingest_dian_xml(tenant_id, raw_xml)`
- `POST /api/v1/shadow-gl/siigo-csv/ingest` → `ingest_siigo_csv(tenant_id, csv_text)`
- `POST /api/v1/shadow-gl/siigo-csv/upload` → same `ingest_siigo_csv`, via multipart file upload,
  additionally tracked in `ingestion_batches`

A fourth path, `_persist_approved_entry()`, re-calls `ingest_dian_xml`/`ingest_siigo_csv` after a
Hermes HITL approval when the *parser* rejected a malformed upload (Phase 6 approval-queue flow,
already live — `shadow_gl_endpoints.py::approval_callback_endpoint`). That path exists to recover
from parse errors, not to distinguish real vs. synthetic data, and is left alone here (see
Non-Goals).

None of the four paths today record whether the ingested data is a genuine Siigo/DIAN export or a
fixture/test upload. Verified against the live DB (2026-08-18): 100% of current rows are
synthetic — see `docs/supabase-mcp-admin.md` §3. Note that "synthetic" is not one uniform category:
29 of the 73 `erp_journal_entries` rows are a deliberate, `pg_cron`-maintained demo seed (migration
`0028`/`0035`) that the live per-tenant Caja Real dashboards depend on — this change flags them
`is_verified_real=false` (correct — they are not real) but does not touch, clean up, or interfere
with the reseed job.

## Goals / Non-Goals

**Goals:**
- Every row in `erp_journal_entries` and `dian_xml_documents` carries an explicit
  `is_verified_real` flag, defaulting to `false`.
- The admin uploading a file can mark it `true` when it's a genuine Siigo/DIAN export, on all
  three direct-upload endpoints.
- Existing 77 rows (73 + 4) are backfilled `false` — none of today's data silently becomes "real."

**Non-Goals:**
- Threading the flag through `_persist_approved_entry()` (the HITL parse-error-recovery replay
  path). That path's `approval_queue.payload.raw_input` doesn't carry the flag today, and adding it
  would touch the Hermes approval-queue message contract — out of scope for a data-integrity flag.
  It keeps inserting with the function default (`false`), which is safe (fail-closed, not
  fail-open).
- Auto-upgrading an existing `false` row to `true` if the same `external_reference_id`/`entry_date`
  is later re-uploaded as real. The idempotency check already skips duplicates before any insert
  happens; changing that to an upsert-with-upgrade is a separate, larger behavior change. If this
  scenario actually happens (unlikely — it requires literally re-uploading the same reference id
  that a fixture once used), fix it with a one-off `UPDATE` in Supabase, not new code.
- Any automated Siigo API integration, RLS/SECURITY DEFINER changes, or tenant/data cleanup — all
  explicitly parked per the proposal's non-goals.

## Decisions

**1. Column on the table, not a separate tracking table.**
A boolean column on `erp_journal_entries`/`dian_xml_documents` was chosen over a new
`verified_ingestions` join table. Rationale: the flag is a property of the row itself (is this
specific journal entry/document real), queries stay a single `WHERE is_verified_real = true`
instead of a join, and it matches the existing pattern of `source`/`uploaded_at` already living
directly on `erp_journal_entries`.

**2. `NOT NULL DEFAULT false`, not nullable.**
A nullable flag (`NULL` = unknown) was considered, but rejected: it would let future code
accidentally treat `NULL` as truthy in a loosely-typed check. `NOT NULL DEFAULT false` makes
"unknown" and "known-fake" the same safe value — nothing is ever accidentally treated as real.

**3. Flag passed as a query parameter, not a header or body field.**
The three endpoints already accept the raw file as the entire request body (`request.body()`) or
as `UploadFile`, so the flag can't live in a JSON body. A query parameter
(`?is_verified_real=true`) is explicit, visible in logs/curl history (useful for the admin runbook,
which already documents curl examples in `docs/admin-runbook-shadow-gl.md`), and doesn't require
restructuring the request parsing.

**4. Default stays `false` at every layer** (DB column default, function parameter default, and
endpoint query-param default). Three independent fail-closed defaults mean a missed flag anywhere
in the chain still lands as `false`, never silently `true`.

## Risks / Trade-offs

- **[Risk]** An admin forgets the `?is_verified_real=true` param when uploading a genuine Siigo
  export → it lands tagged as synthetic, and a later "real ledger" report silently excludes it.
  **Mitigation:** document the flag prominently in `docs/admin-runbook-shadow-gl.md`'s existing curl
  examples (updated as part of this change's tasks), and keep the failure mode safe — a real row
  hiding as "not yet verified" is far less harmful than a fake row appearing as "verified real."
- **[Risk]** Someone flips `is_verified_real=true` on a test upload by mistake.
  **Mitigation:** out of scope to prevent programmatically here (would need auth/role checks this
  change doesn't add); acceptable given today's admin-only, manual-upload-only access model.
- **[Trade-off]** `_persist_approved_entry()` stays flag-blind (see Non-Goals) — an HITL-recovered
  real upload that failed initial parsing lands as `is_verified_real=false` even if it was real.
  Acceptable: this is a narrow edge case (real file + parse failure + HITL override) and can be
  corrected with a manual `UPDATE` if it ever occurs; not worth the added complexity of threading
  the flag through the approval-queue payload today.

## Migration Plan

1. Additive migration (`apps/backend/migrations/`, next sequential number — **check the directory
   directly before numbering**, not memory; a numbering collision already happened once on
   2026-07-23, see `docs/supabase-mcp-admin.md` §6):
   ```sql
   ALTER TABLE erp_journal_entries ADD COLUMN is_verified_real BOOLEAN NOT NULL DEFAULT false;
   ALTER TABLE dian_xml_documents  ADD COLUMN is_verified_real BOOLEAN NOT NULL DEFAULT false;
   ```
   The `DEFAULT false` on the `ALTER TABLE` itself already backfills every existing row — no
   separate `UPDATE` statement is needed (Postgres applies the default to existing rows for a
   `NOT NULL DEFAULT` column add).
2. Update `ingest_dian_xml`/`ingest_siigo_csv` signatures to accept `is_verified_real: bool = False`
   and include it in the inserted row/entry_data dict.
3. Update the three endpoints to read `is_verified_real` from query params and pass it through.
4. Update `docs/admin-runbook-shadow-gl.md` curl examples to show the new param.
5. Update `docs/supabase-mcp-admin.md` §3 once deployed, to reflect the flag is live (not just
   proposed).

**Rollback:** the column is purely additive and nothing reads it yet outside this change, so
rollback is `git revert` + `ALTER TABLE ... DROP COLUMN is_verified_real` on both tables if ever
needed. No data loss risk either direction.

## Open Questions

None blocking — the one real ambiguity (auto-upgrade of existing rows) is resolved as a Non-Goal
above rather than left open.
