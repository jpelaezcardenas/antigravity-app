# Deployment Report — operator-tasks-pulso-insight-constraint-fix

**Date:** 2026-08-29
**Deploy target:** Production Supabase (`kpynymwghfwshvcvevxq`), no Railway/Vercel redeploy needed
**Trigger:** GTM master plan (Envigado Emprende), Fase 0, item 2

## Before

```sql
CHECK ((task_type = ANY (ARRAY['post_content'::text, 'run_ads_ab'::text, 'research'::text,
  'metrics_pull'::text, 'external_integration'::text, 'generate_doc'::text])))
```

Live row count by `task_type`: `post_content` (2), `research` (3). Zero
`pulso_diario_insight` rows — confirming every insert from
`operator_task_service.submit_completed_insight()` had been failing since the
`pulso-diario-agent-insight-bridge` change was archived.

## Migration applied

`apps/backend/migrations/0044_operator_tasks_pulso_insight_type.sql`, applied via Supabase
MCP `apply_migration` (migration name `0044_operator_tasks_pulso_insight_type`).

## After

```sql
CHECK ((task_type = ANY (ARRAY['post_content'::text, 'run_ads_ab'::text, 'research'::text,
  'metrics_pull'::text, 'external_integration'::text, 'generate_doc'::text,
  'pulso_diario_insight'::text])))
```

Verified live via `pg_constraint` query immediately after applying.

## Verification (task 3)

A test insert (`tenant_id` = Cliente Cero, `task_type = 'pulso_diario_insight'`,
`status = 'completed'`) succeeded where it previously would have raised a
`CheckViolation`. The test row was deleted immediately after confirming success — no
synthetic/test data was left in production.

**Not yet exercised:** a real call from Hermes through
`POST /api/v1/agents/pulso-diario/insights` with the actual `HERMES_BRIDGE_TOKEN`. That
endpoint was not called directly in this session to avoid ever placing the live bridge
token value in the visible session transcript (ARCHITECTURE.md §12 hard rule — credential
values never go in versioned files or session notes). The database-layer fix is confirmed;
the full HTTP path will get its first real exercise the next time Hermes actually submits an
insight, which Fase 1/Fase 2 of the GTM plan will surface if it doesn't work.

## Outcome

✅ Constraint fixed and verified live. No application code changes were needed — the bug was
purely a database schema gap. Change ready to archive.
