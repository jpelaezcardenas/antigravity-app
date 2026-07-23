# Implementation report — Section 8 (Migration file), tasks 8.1-8.2

**Scope:** ONLY tasks 8.1 and 8.2 of
`openspec/changes/approval-queue-tenant-scoping/tasks.md`. Tasks 8.3-8.5 (founder
confirmation + live apply + post-apply verification) are explicitly **not** attempted in
this session — no live database access was used, and no Supabase MCP tool
(`apply_migration`, `execute_sql`, etc.) was called.

## 8.1 — Migration file

Created `apps/backend/migrations/0033_approval_queue_tenant_not_null.sql`.

Contract (per `design.md`'s "Migration `0033_approval_queue_tenant_not_null.sql`" section):

1. **Safety re-backfill** — `UPDATE public.approval_queue SET tenant_id = (SELECT id FROM
   public.tenants WHERE is_cliente_cero = TRUE) WHERE tenant_id IS NULL OR tenant_id =
   '00000000-0000-0000-0000-000000000000';` — a documented no-op today per the live
   verification query already run and recorded in `design.md`'s "Pre-work verification
   (2026-07-23)" section (6/6 rows already carry the real Cliente Cero UUID, no NULL/zeros
   rows). Kept so the migration stays correct if it's ever re-run against a regressed
   database.
2. **`DROP DEFAULT`**, idempotency-guarded — wrapped in a `DO $$ BEGIN ... END $$;` block
   that checks `information_schema.columns.column_default IS NOT NULL` for
   `(table_schema='public', table_name='approval_queue', column_name='tenant_id')` before
   issuing `ALTER TABLE public.approval_queue ALTER COLUMN tenant_id DROP DEFAULT;`. This
   mirrors the exact `information_schema.columns` guard idiom used in
   `0001_add_tenant_id_columns.sql` (checks `column_name` existence before `ADD COLUMN`) and
   `0003_enable_rls_policies.sql`'s general "check state before mutating" style. Re-running
   this block after the default is already dropped is a no-op (the `EXISTS` check is false),
   never an error.
3. **`SET NOT NULL`**, unguarded — verified PostgreSQL's documented behavior: `ALTER COLUMN
   ... SET NOT NULL` on a column that is already `NOT NULL` re-validates and succeeds
   silently (no error), so it is safely idempotent without a `DO $$` wrapper. Used the
   simplest correct form per the task instructions.

Header comment block matches the repo's migration style (`Migration:` / `Date:` /
`Purpose:` / `Idempotent:` / `Prerequisites:` lines, plus a note citing the live pre-work
verification), following the format used in `0001`-`0003`.

## 8.2 — Validation

Checked for a `migrate:test` npm script (per CLAUDE.md's documented convention:
`npm run migrate:test`) at every `package.json` in the repo:

```
$ find . -maxdepth 3 -name "package.json"
./contexia-app/package.json
./contexia-wizard/package.json
./frontend/dashboard/package.json
./package.json

$ grep -rn "migrate:test" --include=package.json .
(no matches)
```

- Root `package.json` only has a `build` script (`"echo 'No build needed'"`) — no
  `migrate:test`.
- No `apps/backend/package.json` exists at all (backend is Python/FastAPI, no npm scripts
  live there).
- None of `contexia-app/`, `contexia-wizard/`, `frontend/dashboard/` define `migrate:test`
  either — none of them own backend migrations.

**Conclusion: no `migrate:test` script exists in this repo.** This confirms the task's
documented fallback applies — did a **static SQL syntax review** instead:

- Read the finished file back in full and manually verified:
  - Exactly one `DO $$ ... END $$;` block, correctly opened/closed, with a nested
    `IF EXISTS (...) THEN ... END IF;` also correctly balanced.
  - Every statement (the `UPDATE`, the `ALTER TABLE ... DROP DEFAULT`, the `ALTER TABLE ...
    SET NOT NULL`) terminated with a semicolon.
  - No dangling `$$` delimiters or unmatched parens in the subquery
    `(SELECT id FROM public.tenants WHERE is_cliente_cero = TRUE)`.
  - `information_schema.columns` guard columns/predicates match the exact pattern already
    proven live-safe in `0001_add_tenant_id_columns.sql` (same `table_schema`/`table_name`/
    `column_name` triple, same `SELECT 1 FROM ... WHERE ...` shape).
  - Table/column names (`public.approval_queue`, `tenant_id`) match every other migration
    that touches this table (`0001`, `0002`, `0003`, `0017`).
  - The Cliente Cero lookup subquery (`SELECT id FROM public.tenants WHERE is_cliente_cero =
    TRUE`) matches the live-verified resolution pattern already used elsewhere in this
    codebase (`resolve_cliente_cero_tenant_id`) rather than hardcoding the UUID literal (the
    task explicitly specified this dynamic-lookup form, unlike migration `0002`'s hardcoded
    literal).

No syntax issues found. This is a static review only — it does not (and per the task's
explicit instruction, must not) execute against any live database.

## Not attempted (out of this session's authorization)

- Task 8.3: asking the founder for confirmation — left unchecked, to be handled by the
  orchestrating session.
- Task 8.4: applying the migration to Supabase project `kpynymwghfwshvcvevxq` — not
  attempted; no Supabase MCP tool was called at any point in this session.
- Task 8.5: re-running the post-apply verification query — not applicable, nothing was
  applied.

## Files touched

- `apps/backend/migrations/0033_approval_queue_tenant_not_null.sql` (new)
- `openspec/changes/approval-queue-tenant-scoping/tasks.md` (checked off 8.1, 8.2 only)
- `progress/impl_section8_migration_file.md` (this report)

## Verification commands run

```
$ find . -maxdepth 3 -name "package.json"
$ grep -rn "migrate:test" --include=package.json .
```

Both confirm no `migrate:test` script exists anywhere in the repo — documented above as the
basis for falling back to static SQL review.
