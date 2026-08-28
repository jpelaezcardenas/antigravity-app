# Proposal: pulso-diario-agent-insight-bridge

## Why

`GET /api/v1/financials` returns a zeroed `status: "empty"` snapshot whenever a resolved tenant
has no Shadow GL rows yet. For a freemium tenant without an opening-balance seed (the optional
step added by `freemium-tenant-minimum-seed`) and without real Siigo/DIAN ingestion, this is the
permanent state — `CashTodayCard` never shows anything beyond "Sin datos aún." The master plan's
Subdomain 6 closes this durably: let a Hermes agent push a computed "Pulso Diario" insight for a
tenant, and have the backend serve it as a fallback exactly when Shadow GL is empty — without
touching the Shadow GL path that already works for every existing client.

## What Changes

- Reuses the existing `operator_tasks` queue (Change F) with a new read-only `task_type`:
  `pulso_diario_insight`. An agent submits a **pre-completed** task (there is no "pending" step to
  claim — this is unsolicited push, not a dispatched request) via a new bridge-token-gated
  endpoint.
- New `POST /api/v1/pulso-diario/insights` (gated by the existing
  `require_hermes_bridge_token` dependency, reused from `sell_machine_endpoints.py`) — an agent
  submits `{tenant_id, caja_real, dinero_disponible, ventas_ayer, gastos_ayer}` (same 5-key shape
  as `compute_pulso_daily_snapshot`, minus `status`), stored as a `completed` `operator_tasks` row.
- `GET /api/v1/financials` gains an internal fallback: when `compute_pulso_daily_snapshot` returns
  `status: "empty"` for a resolved tenant, the endpoint checks for the tenant's latest completed
  `pulso_diario_insight` task and, if one exists, returns it instead (with `status: "healthy"` and
  an additional `source: "agent_insight"` field) — Shadow GL-backed tenants are entirely
  unaffected (this branch is only reached when Shadow GL itself has nothing).
- `operator_task_service.py` gains `submit_completed_insight()` (bypasses the pending→dispatched
  state machine, since there's no correlated pending task) and `list_completed_tasks()` gains an
  optional `tenant_id` filter.
- No frontend change: `CashTodayCard` already renders any `status: "healthy"` snapshot identically
  regardless of its origin — the fallback is fully transparent to the PWA.

## Capabilities

### New Capabilities
- `pulso-diario-agent-insight` — the new bridge-token-gated ingestion endpoint and its
  `operator_tasks` contract.

### Modified Capabilities
- `pulso-financials-api` — `GET /api/v1/financials`'s empty-snapshot behavior gains the fallback
  described above (delta below).

## Impact

- `apps/backend/services/operator_task_service.py` — new `submit_completed_insight()`,
  `list_completed_tasks(tenant_id=...)`.
- `apps/backend/presentation/pulso_diario_endpoints.py` — new `POST /insights` route (the
  existing `/summary` stub is untouched — out of scope, still a stub, not this change's concern).
- `apps/backend/presentation/financials_endpoints.py` — `get_financials`'s empty-tenant branch
  gains the fallback lookup.
- No migration — reuses the existing `operator_tasks` table as-is.
