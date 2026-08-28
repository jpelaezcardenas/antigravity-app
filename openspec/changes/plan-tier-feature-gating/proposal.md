## Why

Subdomain 3 of the freemium-onboarding master plan. Today, "plan tier" is not a real concept
anywhere in live code: `tenants` has no tier column, `b2b_clients` has none either, the only
tier-shaped artifact in the repo (`plan_type` ENUM, migration `0010`) types a column on an
unrelated table (`customer_invites`) and is never read by any live endpoint, and the Config page's
"Plan Starter · Activo" is a hardcoded string with zero backend behind it. Without a real,
enforced tier, there is no way to onboard a freemium client whose access is actually limited to
Pulso Diario — every provisioned tenant today sees everything. This blocks Subdomains 4 and 5.

## What Changes

- Add a `plan_tier` column (`text` + `CHECK`, not a new Postgres ENUM) to `tenants`, mirrored on
  `b2b_clients`, defaulting every existing and new row to `'starter'` — so no currently-provisioned
  client loses access the moment this ships.
- Add `apps/backend/core/plan_features.py`: an explicit tier -> allowed-features map. `freemium`
  gets only `pulso_diario`; `starter`/`growth`/`enterprise` get every feature that exists today
  (`pulso_diario`, `centinela_alerts`, `liquidity_bridge`). An unrecognized/missing tier value
  fails **open** (full access) — see `design.md` Decisions for why.
- Gate the 3 real, data-bound PWA endpoints by feature: `GET /api/v1/financials`,
  `GET /api/v1/centinela/alerts`, `GET /api/v1/financials/liquidity-bridge`. Each gains an explicit
  `not_in_plan`-shaped response, added as one more branch inside each endpoint's/component's
  *existing* status handling — no new UI pattern invented.
- Add `GET /api/v1/tenant/me` (`{legal_name, plan_tier}`), tenant-scoped via the canonical
  `resolve_request_tenant_scope`, so the Config page can stop hardcoding "Plan Starter · Activo".
- Add a plan-gated "upgrade your plan" prompt to the 3 mock screens (Fiscal, Radar, Patrimonio)
  when the resolved tenant's tier is `freemium` — these screens stay 100% mock otherwise; this
  change does not wire them to real data.

## Capabilities

### New Capabilities
- `plan-tier-feature-gating`: the `tenants.plan_tier` column, the `core/plan_features.py`
  tier-to-feature map, and the new `GET /api/v1/tenant/me` endpoint.

### Modified Capabilities
- `pulso-financials-api`: `GET /api/v1/financials` and `GET /api/v1/financials/liquidity-bridge`
  gain a plan-tier feature check before computing their snapshot.
- `centinela-alerts`: `GET /api/v1/centinela/alerts` gains a plan-tier feature check before
  querying `centinela_alerts`. The legacy `GET /centinela/alerts/{company_id}` (Hermes-consumed) is
  explicitly **not** gated — out of scope, per that spec's own "legacy route is unaffected"
  scenario.

## Impact

- New migration `apps/backend/migrations/0043_add_plan_tier.sql`.
- New file `apps/backend/core/plan_features.py`.
- Modified: `apps/backend/presentation/financials_endpoints.py`,
  `apps/backend/presentation/centinela_endpoints.py`, plus a new
  `apps/backend/presentation/tenant_endpoints.py` (or equivalent) for `GET /api/v1/tenant/me`.
- Modified: `contexia-app/components/pulso/CashTodayCard.tsx`,
  `contexia-app/components/pulso/ActiveAlerts.tsx`,
  `contexia-app/components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx`,
  `contexia-app/app/app/(shell)/config/page.tsx`,
  `contexia-app/app/app/(shell)/fiscal/page.tsx`,
  `contexia-app/app/app/(shell)/radar/page.tsx`,
  `contexia-app/app/app/(shell)/patrimonio/page.tsx`,
  `contexia-app/lib/api-client.ts`, `contexia-app/lib/config.ts`.
- Does **not** touch the B2B "Alta" form (`B2bRetainersTab.tsx`) or `crm_service.py` — wiring a
  tier selector into client onboarding is Subdomain 4 (`crm-alta-tiered-provisioning`), a separate
  change that depends on this one.
- No pricing numbers are introduced anywhere — only tier names and feature membership.
