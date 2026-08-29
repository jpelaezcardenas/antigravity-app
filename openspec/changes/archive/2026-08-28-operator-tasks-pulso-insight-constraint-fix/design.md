## Context

`operator_tasks` is a generic queue (migration `0024`) used by two independent producers:
the Sell Machine dispatch flow (`post_content`, `run_ads_ab`, `research`, `metrics_pull`,
`external_integration`, `generate_doc`) and, since the `pulso-diario-agent-insight-bridge`
change, Hermes pushing a computed Pulso Diario insight for tenants with empty Shadow GL
(`submit_completed_insight()` in `operator_task_service.py`). That second producer writes
`task_type='pulso_diario_insight'` directly with `status='completed'` (it bypasses the normal
pending→dispatched state machine by design, since Hermes already computed the result). The
original migration's CHECK constraint was never updated when that capability was built, so
every insert has been rejected by Postgres in production. Confirmed live: the constraint
excludes the value, and the table has zero rows of this type.

## Goals / Non-Goals

**Goals:**
- Make `pulso_diario_insight` a valid `task_type` at the database layer, matching what the
  application code already assumes.
- Ship as the smallest possible change: one additive migration, no application code touched.

**Non-Goals:**
- Not revisiting the overall `operator_tasks` state-machine design (pending/dispatched/
  completed/failed) — `submit_completed_insight()`'s bypass-to-completed pattern is accepted
  as-is; it was a deliberate design choice in the original change, not something this fix
  reopens.
- Not adding a dedicated table for insights. Reusing the generic queue is the existing
  pattern for read-only agent outputs (`research`, `metrics_pull` behave the same way).

## Decisions

- **Widen the existing CHECK constraint rather than drop it / make the column an enum.**
  A text CHECK is the pattern every other migration on this table already uses; switching to
  a Postgres enum here would be a larger, riskier change for a one-value fix with no other
  driver.
- **New migration, not editing `0024` in place.** Migrations are append-only in this repo
  (confirmed pattern: `0034` rescoped `0033`'s output via a *new* migration, never an edit of
  an applied one). `0044` follows directly after the latest applied migration (`0043_add_plan_tier.sql`).

## Risks / Trade-offs

- [Risk] Another session could pick the same migration number (`0044`) concurrently → collision,
  same class of incident as the `0033`/`0034` numbering conflict documented in
  ARCHITECTURE.md Decision #15. Mitigation: verify no `0044_*.sql` exists immediately before
  writing the file, and re-check right before applying to production.
- [Risk] `ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT` takes a brief lock on
  `operator_tasks`. Mitigation: table has 5 rows total today — negligible; run outside of no
  other special window needed.
- [Trade-off] Not backfilling anything — this only unblocks *future* inserts. Any Hermes calls
  that already failed silently are not retried automatically; Fase 1 verification will trigger
  a fresh real insight submission from Hermes to confirm the fix end-to-end.

## Migration Plan

1. Write `apps/backend/migrations/0044_operator_tasks_pulso_insight_type.sql`.
2. Apply to production Supabase (`kpynymwghfwshvcvevxq`) via the Supabase MCP `apply_migration`
   (DDL-safe path, not `execute_sql`).
3. Re-run the constraint-definition query used in Fase 0 diagnosis to confirm the new value is
   present.
4. Trigger one real `POST /api/v1/agents/pulso-diario/insights` call (or ask Hermes to) and
   confirm a row lands with `task_type='pulso_diario_insight'`.
5. Stage 11: no frontend/backend redeploy needed (no app code changed) — the deployment report
   documents the migration application itself as the "deploy."

Rollback: `ALTER TABLE operator_tasks DROP CONSTRAINT chk_operator_tasks_task_type_v2, ADD
CONSTRAINT chk_operator_tasks_task_type CHECK (...)` restoring the original 6-value list —
safe only if no `pulso_diario_insight` rows exist yet at rollback time (true until step 4 runs).
