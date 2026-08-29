## Why

`operator_task_service.submit_completed_insight()` inserts rows with
`task_type='pulso_diario_insight'`, but the live `operator_tasks` CHECK constraint
(`chk_operator_tasks_task_type`, defined in migration `0024_operator_tasks.sql`) never
allowed that value — it only permits `post_content`, `run_ads_ab`, `research`,
`metrics_pull`, `external_integration`, `generate_doc`. Confirmed live against production
Supabase (`kpynymwghfwshvcvevxq`): the constraint definition excludes the value, and zero
`pulso_diario_insight` rows exist in the table despite the bridge (`pulso-diario-agent-insight`
change) having been archived as complete. Every call to
`POST /api/v1/agents/pulso-diario/insights` from Hermes has been failing at the database layer
since deploy. This blocks Fase 0 of the approved GTM master plan (Envigado Emprende
presentation) — the fallback path that lets a tenant without Shadow GL data still show a real
Pulso Diario insight is currently dead in production.

## What Changes

- Widen `chk_operator_tasks_task_type` to also allow `'pulso_diario_insight'`, via a new
  migration (`0044_operator_tasks_pulso_insight_type.sql`, next in sequence after
  `0043_add_plan_tier.sql`).
- No application code changes — `operator_task_service.submit_completed_insight()` already
  inserts the correct value; only the database was out of sync with it.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `pulso-diario-agent-insight`: the persistence requirement ("Hermes can submit a completed
  Pulso Diario insight via the bridge token endpoint") now actually holds at the database
  layer — today it is documented as working but silently fails on every insert.

## Impact

- `apps/backend/migrations/0044_operator_tasks_pulso_insight_type.sql` (new file).
- Production Supabase schema (`operator_tasks` table) — DDL applied via migration.
- No API, frontend, or Hermes/poller code changes required.
