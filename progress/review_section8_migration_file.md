# Review — task section8_migration_file

**Verdict:** APPROVED

## Checkpoints

- C1 (SQL validity): [x] `0033_approval_queue_tenant_not_null.sql` is syntactically valid PG.
  One `DO $$ BEGIN ... END $$;` block (lines 30-41), nested `IF EXISTS (...) THEN ... END IF;`
  correctly balanced, every statement terminated with `;`.
- C2 (style consistency with 0001/0002/0003): [x] Header comment block matches the
  `Migration:`/`Date:`/`Purpose:`/`Idempotent:`/`Prerequisites:` convention. The
  `information_schema.columns` guard idiom (schema/table/column triple) mirrors
  0001's `ADD COLUMN` guard exactly. `SET NOT NULL` left unguarded on the documented,
  correct rationale that PG re-validates idempotently — consistent with 0003's
  "state-check before mutating, but only where actually needed" style.
- C3 (safety re-backfill failure mode): [x] Verified rigorously.
  - Zero `is_cliente_cero=TRUE` rows → subquery is a NULL scalar → UPDATE sets
    `tenant_id = NULL` on matching rows → step 3 (`SET NOT NULL`) then fails loudly.
    Safe: no silent corruption, migration aborts.
  - Multiple `is_cliente_cero=TRUE` rows (no unique constraint exists on that column
    anywhere in `apps/backend/migrations/` — checked all 32 files) → the scalar subquery
    raises PG's own `more than one row returned by a subquery used as an expression`
    at the UPDATE itself → transaction aborts, loud and safe.
  - Note: sibling migrations (`0021`, `0023`, `0028`) use `... WHERE is_cliente_cero = true
    LIMIT 1` for the same lookup; `0033` intentionally omits `LIMIT 1`. This is not a bug —
    for a *hardening* migration, silently picking one of several Cliente Cero rows via
    `LIMIT 1` would mask a real data-integrity violation; failing loudly is the more correct
    choice here. Flagging as a deliberate, justified deviation, not a defect.
  - `design.md` "Pre-work verification (2026-07-23)" confirms the live table has exactly one
    tenant group today (6/6 rows on the real Cliente Cero UUID), so this is a no-op on current
    data — matches the migration's own header comment.
- C4 (DROP DEFAULT before SET NOT NULL ordering): [x] No PG quirk — `SET NOT NULL` only
  checks for NULL values, independent of column default. Order is correct/idiomatic.
- C5 (DO $$ guard correctness): [x] Filters on `table_schema='public'`, `table_name=
  'approval_queue'`, `column_name='tenant_id'`, `column_default IS NOT NULL` — correct triple,
  matches 0001's pattern.
- C6 (does not touch `approval_queue_anon_all`): [x] Confirmed — file has no `DROP POLICY` /
  `ALTER POLICY` statement; only touches `tenant_id` column constraints. Consistent with
  `design.md`'s explicit deferral of the permissive-policy question.
- C7 (no live apply this session): [x] `progress/impl_section8_migration_file.md` explicitly
  states no Supabase MCP tool was called; only local `find`/`grep` commands were run
  (documented at lines 45-53, 104-107). The one live query referenced (`design.md`'s "Pre-work
  verification") predates this commit and was already recorded as a design artifact, not
  re-run here.
- C8 (scope discipline): [x] `git show 97c41b1 --stat` — exactly 3 files: the new migration,
  `openspec/changes/approval-queue-tenant-scoping/tasks.md` (diff confirms only 8.1/8.2 boxes
  checked, 8.3-8.5 left `[ ]`), and `progress/impl_section8_migration_file.md`.
- Docs-sync: [x] N/A — no container/dependency change; migration is schema-internal to an
  already-documented tenant-scoping effort (ARCHITECTURE.md Decision #13 already covers
  per-tenant resolution; this migration only hardens the existing contract).

## Required changes

None.
