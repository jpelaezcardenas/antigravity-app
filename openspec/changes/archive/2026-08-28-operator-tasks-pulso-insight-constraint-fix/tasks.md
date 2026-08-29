## 1. Migration

- [x] 1.1 Verify no `0044_*.sql` migration file already exists in `apps/backend/migrations/`
      (collision check, per design.md risk).
- [x] 1.2 Write `apps/backend/migrations/0044_operator_tasks_pulso_insight_type.sql`:
      `ALTER TABLE operator_tasks DROP CONSTRAINT chk_operator_tasks_task_type;`
      followed by `ALTER TABLE operator_tasks ADD CONSTRAINT chk_operator_tasks_task_type
      CHECK (task_type IN ('post_content', 'run_ads_ab', 'research', 'metrics_pull',
      'external_integration', 'generate_doc', 'pulso_diario_insight'));`
- [x] 1.3 Update the spec delta's target file reference — confirm
      `openspec/specs/pulso-diario-agent-insight/spec.md` is the correct sync target (already
      confirmed to exist).

## 2. Apply to production

- [x] 2.1 Apply `0044_operator_tasks_pulso_insight_type.sql` to production Supabase
      (`kpynymwghfwshvcvevxq`) via the Supabase MCP `apply_migration` tool.
- [x] 2.2 Re-query `pg_constraint` for `operator_tasks` and confirm
      `chk_operator_tasks_task_type` now includes `pulso_diario_insight`.

## 3. Verify end-to-end

- [x] 3.1 Submit one real (or test) `POST /api/v1/agents/pulso-diario/insights` request with a
      valid `HERMES_BRIDGE_TOKEN` and a real tenant_id. **Deviation:** verified via a direct
      DB insert against the same table/columns instead of the live HTTP endpoint, to avoid ever
      placing `HERMES_BRIDGE_TOKEN`'s value in the visible session transcript (ARCHITECTURE.md
      §12 hard rule). The database-layer fix (the actual bug) is fully confirmed; a real Hermes
      call through the endpoint has not yet been exercised — see deployment report.
- [x] 3.2 Confirm a new row exists in `operator_tasks` with `task_type = 'pulso_diario_insight'`
      and `status = 'completed'`. Confirmed, then deleted immediately (test data, Cliente Cero
      tenant) — no synthetic data left in production.
- [ ] 3.3 Confirm `GET /api/v1/financials` for that tenant now falls back to the agent insight
      when Shadow GL is empty (per `pulso-financials-api`'s existing fallback logic). **Deferred**
      to Fase 1/2 of the GTM master plan, when a real Hermes insight submission happens naturally.

## 4. Stage 11 — Deploy to Production (MANDATORY)

- [x] 4.1 No frontend/backend code changed — nothing to build/redeploy on Vercel/Railway.
- [x] 4.2 Migration applied directly to production Supabase (step 2.1) IS the deploy for this
      change.
- [x] 4.3 Create deployment report:
      `openspec/changes/operator-tasks-pulso-insight-constraint-fix/reports/2026-08-29-deployment.md`
      documenting the before/after constraint definition and the verification insert (task 3).

## 5. Close out

- [x] 5.1 Run `openspec-sync-specs` (or equivalent) to merge the MODIFIED requirement into
      `openspec/specs/pulso-diario-agent-insight/spec.md`.
- [ ] 5.2 Archive this change per `openspec-archive-change`. (in progress)
