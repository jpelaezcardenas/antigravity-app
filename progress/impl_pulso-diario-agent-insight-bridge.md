# Implementer report — pulso-diario-agent-insight-bridge

- Date: 2026-08-28
- Scope: full change (Sections 1-4 of tasks.md), TDD throughout.

## Investigation (delegated to an Explore agent, then verified directly)

Confirmed both endpoints named in the master plan's own text
(`/api/v1/agents/pulso-diario/summary`, `/api/v1/pulso/{usuario_id}` and `/today`) are genuine
stubs — none reads Shadow GL or any real data. There is no existing "agent produces an insight ->
PWA" pipeline. Design decision (design.md D1-D4): reuse the existing `operator_tasks` queue with a
new `task_type="pulso_diario_insight"`, created directly as `completed` (push, not the existing
pending->dispatched->completed request/response lifecycle, which doesn't fit an unsolicited local
push); reuse `require_hermes_bridge_token` as-is (already hardened in Subdomain 1); wire the
fallback entirely inside `financials_endpoints.py::get_financials` so `CashTodayCard` needs zero
changes (it already renders any `status: "healthy"` payload identically).

## Section 1 — `operator_task_service.py`

TDD: 4 new tests (`TestSubmitCompletedInsight`, `TestListCompletedTasksTenantFilter`) red first
(`ImportError` on the new names), then implemented `submit_completed_insight()` (direct
`completed` insert, validates `tenant_id` via the existing `tenant_exists` helper — no Cliente
Cero fallback, an insight with no tenant is a caller bug) and extended `list_completed_tasks()`
with an optional `tenant_id` filter (mirrors `list_pending_tasks`'s existing pattern). One test
bug found and fixed along the way: the tenant-isolation test's mock chain asserted on the wrong
`.eq()` level (two chained `.eq()` calls, not one, before the tenant_id filter) — fixed to assert
on the correct third-level mock. 26/26 tests in the file green.

## Section 2 — `POST /api/v1/agents/pulso-diario/insights`

TDD: 4 new tests (`test_pulso_diario_insight_endpoint.py`, httpx `ASGITransport` pattern — never
the broken `starlette` `TestClient`) red first, then implemented in
`pulso_diario_endpoints.py`, importing `require_hermes_bridge_token` directly from
`presentation.sell_machine_endpoints` (no duplication — same actor, same kind of local-to-cloud
push). Mounted under the existing `/agents/pulso-diario` prefix rather than a new router, since
this file already owns that mount point. 4/4 green.

## Section 3 — `GET /api/v1/financials` fallback

TDD: 4 new tests (`test_financials_agent_insight_fallback.py`, pure-mock, no real Supabase) plus
one existing test (`test_staging_identity_falls_back_to_cliente_cero`) updated to monkeypatch the
new `list_completed_tasks` import — otherwise it would have made a real, unmocked Supabase call
from what was previously a pure-unit test (disclosed, not silently patched). Implemented
`_latest_agent_insight_snapshot()`: only invoked when `compute_pulso_daily_snapshot` itself
returns `status: "empty"` for a resolved tenant (never for "no tenant resolved" — that still goes
through the existing non-leaking `_empty_snapshot()` untouched); picks the latest completed
`pulso_diario_insight` task by `created_at`, validates the result shape defensively (fails closed
to `None`, same pattern as `sell_machine_service.py::get_latest_manus_draft()`), and returns it
with `status: "healthy"` + a new `source: "agent_insight"` field. 8/8 green (4 new + 4 existing
tenant-scoping tests, 2 of which hit a real live Supabase connection in this environment and
passed unaffected).

## Section 4 — Testing

Broader sweep in progress at report time (`-k "operator_task or financials or pulso_diario"`,
excluding the same 3 pre-existing `ModuleNotFoundError: No module named 'apps'` files as prior
subdomains) — see reviewer pass for the confirmed final count.

## Files touched

- Modified: `apps/backend/services/operator_task_service.py`,
  `apps/backend/presentation/pulso_diario_endpoints.py`,
  `apps/backend/presentation/financials_endpoints.py`,
  `apps/backend/tests/test_operator_task_service.py` (6 new tests),
  `apps/backend/tests/test_financials_endpoint_tenant_scoping.py` (1 test updated for the new
  `list_completed_tasks` dependency).
- New: `apps/backend/tests/test_pulso_diario_insight_endpoint.py`,
  `apps/backend/tests/test_financials_agent_insight_fallback.py`,
  `openspec/changes/pulso-diario-agent-insight-bridge/` (proposal, design, 2 specs, tasks).

## No frontend change

Deliberate (design.md D3): `CashTodayCard` already renders any `status: "healthy"` payload
identically regardless of origin. Adding a visible "estimated"/agent-sourced badge is a real
product decision the founder hasn't made; `source: "agent_insight"` is present in the API response
for any future frontend work to key off.

## Next step

Awaiting reviewer pass before Stage 11 (deploy + report) and archive.
