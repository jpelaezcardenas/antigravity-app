# Tasks: pulso-diario-agent-insight-bridge

## 1. `operator_task_service.py` — new insight primitives (TDD)

- [ ] 1.1 Write failing tests: `submit_completed_insight(tenant_id, result)` creates a `completed`
      `operator_tasks` row with `task_type="pulso_diario_insight"` directly (no pending/dispatched
      hop); rejects an unknown `tenant_id`.
- [ ] 1.2 Write failing tests: `list_completed_tasks(task_type=..., tenant_id=...)` filters by
      both when given; tenant isolation (T1's tasks never returned for T2).
- [ ] 1.3 Implement both in `apps/backend/services/operator_task_service.py`.
- [ ] 1.4 Tests green.

## 2. New endpoint: `POST /api/v1/pulso-diario/insights`

- [ ] 2.1 Write failing tests: valid bridge token + payload → 200, row created; missing/invalid
      token → 401, no row created; unknown tenant_id → error, no row created.
- [ ] 2.2 Implement in `apps/backend/presentation/pulso_diario_endpoints.py`, reusing
      `require_hermes_bridge_token` (import from `presentation.sell_machine_endpoints`).
- [ ] 2.3 Tests green.

## 3. `GET /api/v1/financials` fallback wiring

- [ ] 3.1 Write failing tests: Shadow GL `status: "empty"` + a completed insight for that tenant →
      returns the insight (`status: "healthy"`, `source: "agent_insight"`); Shadow GL `"empty"` +
      no insight → unchanged zeroed empty snapshot; Shadow GL non-empty (`"healthy"`) → fallback
      lookup never invoked; no tenant resolved at all → zeroed empty snapshot regardless of any
      insight data.
- [ ] 3.2 Implement the fallback branch in
      `apps/backend/presentation/financials_endpoints.py::get_financials`.
- [ ] 3.3 Tests green.

## 4. Testing

- [ ] 4.1 Run full backend suite (`-k "operator_task or financials or pulso_diario"` plus a
      broader sweep) — confirm no regressions.

## 5. Reports

- [ ] 5.1 Write `progress/impl_pulso-diario-agent-insight-bridge.md`.

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green) — no frontend change in this file set, but Vercel
      redeploys on every push to main; confirm it stays green
- [ ] 11.3 Railway deploy active (backend change)
- [ ] 11.4 Production URL: `POST /pulso-diario/insights` requires auth (401 unauthenticated),
      `GET /financials` still works for existing tenants
- [ ] 11.5 Create report: openspec/changes/pulso-diario-agent-insight-bridge/reports/YYYY-MM-DD-deployment.md
