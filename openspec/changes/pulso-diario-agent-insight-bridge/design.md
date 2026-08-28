# Design: pulso-diario-agent-insight-bridge

## Context

Investigation confirmed both candidate "real" endpoints named in the master plan
(`/api/v1/agents/pulso-diario/summary` and `/api/v1/pulso/{usuario_id}` /`/today`) are stubs —
neither reads Shadow GL nor anything else real. There is no existing "agent produces an insight
that feeds the PWA" pipeline to build on; this change designs it from scratch, reusing the
existing `operator_tasks` queue and `require_hermes_bridge_token` guard (both from
`hermes-manus-execution-bridge`) rather than inventing new infrastructure.

## Decision D1 — Push, not poll: no pending/dispatched hop

The existing `operator_tasks` lifecycle (`pending` → `dispatched` → `completed`) models Contexia
*asking* Hermes to do something (e.g. dispatch a campaign). Pulso Diario insight generation is the
opposite direction: Hermes runs on its own local schedule and *pushes* a result Contexia never
asked for at that specific moment. Forcing this through `create_task` (pending) +
`mark_dispatched` + `report_result` would be three round trips for something that is, from
Contexia's side, a single fact. `submit_completed_insight()` inserts an `operator_tasks` row
directly with `status="completed"`, `task_type="pulso_diario_insight"` — skipping the
pending/dispatched states entirely, since nothing in this system ever "dispatched" it.

## Decision D2 — Reuse `require_hermes_bridge_token`, not a new auth mechanism

`sell_machine_endpoints.py::require_hermes_bridge_token` already exists, is already hardened
(Subdomain 1, `hermes-bridge-token-production-hardening`), and is exactly the right primitive: a
local, on-prem Hermes process authenticating to a small number of bridge routes with a shared
bearer token. Importing it into the new `pulso_diario_endpoints.py` route avoids a second parallel
auth mechanism for what is conceptually the same actor (Hermes) doing the same kind of thing
(pushing results across the local↔cloud boundary).

## Decision D3 — Fallback lives entirely in the backend; `CashTodayCard` is untouched

`compute_pulso_daily_snapshot`'s 5-key return shape (`caja_real`, `dinero_disponible`,
`ventas_ayer`, `gastos_ayer`, `status`) is exactly what `CashTodayCard`'s `toCashToday()` mapper
already consumes. Rather than adding a second fetch call and a new frontend state (as the master
plan's text originally sketched), the fallback is inserted inside `get_financials` itself: when
the real Shadow GL computation yields `status: "empty"` for a **resolved** tenant (never for the
"no tenant resolved" case — Decision from `per-tenant-client-access` still applies, no fallback
ever substitutes for a missing tenant), look up the tenant's latest completed
`pulso_diario_insight` task and, if found, return its payload as a `status: "healthy"` snapshot
with one added field, `source: "agent_insight"`.

**Why no frontend change**: `CashTodayCard` renders identically for any `status: "healthy"`
payload regardless of origin — it has no notion of "is this Shadow GL or an agent." Adding a
visible "estimated" badge is a real product decision (do we want a freemium user to know their
number came from an agent estimate vs. real ledger data?) that the founder hasn't made; until
that's decided, showing accurate real numbers (an agent-computed insight is real data, not
fabricated — unlike the mock-fallback the codebase's hard rule forbids) without a special badge is
the safe default. `source: "agent_insight"` is present in the API response for any future frontend
work to key off, without forcing a UI decision into this change.

**Why Shadow GL-backed tenants are unaffected**: the fallback lookup only runs inside the
`status == "empty"` branch, which for those tenants never happens — Cliente Cero and the 10
existing B2B clients keep behaving exactly as before.

## Decision D4 — `list_completed_tasks` gains a `tenant_id` filter

Today `list_completed_tasks(task_type=None)` has no tenant filter — fine for Sell Machine (Cliente
Cero-scoped), wrong for Pulso Diario insights (must never leak tenant A's insight to tenant B).
Adds an optional `tenant_id` param, applied via `.eq("tenant_id", tenant_id)` alongside the
existing `task_type` filter — mirrors `list_pending_tasks`'s existing pattern exactly.

## Out of scope

- `/api/v1/agents/pulso-diario/summary` and `/api/v1/pulso/*` — confirmed stubs, untouched by this
  change; they are unrelated code paths, not this pipeline's entry point.
- Any frontend badge/label distinguishing agent-insight data from Shadow GL data — deferred, see
  D3.
- The actual Hermes-side cron/schedule that would call `POST /pulso-diario/insights` — that is
  Hermes-side automation (local/on-prem, outside this repo per ARCHITECTURE.md Decision #1);
  this change only builds the receiving contract Contexia's backend exposes.
- Historical/multi-day insight tracking — only the latest completed insight per tenant is ever
  read; older ones remain in `operator_tasks` for audit but are never surfaced.
