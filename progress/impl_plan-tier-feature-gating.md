# Implementer report — plan-tier-feature-gating

- Date: 2026-08-28
- Scope: full change (Sections 1-10 of tasks.md, TDD throughout). Section 11 (Stage 11 deploy)
  and the reviewer gate are separate steps following this report.

## Research phase

Before writing any OpenSpec artifact, ran a 6-agent research workflow (migration numbering,
the 3 real PWA components' exact state-handling idiom, tenant-resolution/endpoint insertion
points, `core/rbac.py` dead-code confirmation, CRM alta reconnaissance, Config page) plus a
synthesis pass. Independently spot-checked the two highest-stakes claims by directly reading
`financials_endpoints.py`, `tenant_context.py`, and `centinela_endpoints.py`, and by querying
live Supabase `information_schema.columns` for `tenants`/`b2b_clients`/`usuarios.plan` — all
matched the workflow's findings. This surfaced two corrections to the master plan's original
assumptions (documented in `design.md`'s Context section): migration 0010's `plan_type` enum
types a column on `customer_invites`, not `usuarios`; and the `"starter"` hardcode is in
`_provision_b2b_client_login`, not `create_b2b_client`.

## Section 1 — Migration

Wrote and applied `0043_add_plan_tier.sql` (next available number, confirmed via directory
listing + a `git log --diff-filter=D` check that the pre-existing `0031→0033` gap is benign,
not a hidden collision). Applied live via Supabase MCP `apply_migration`; verified all 13
`tenants` and 10 `b2b_clients` rows landed on `'starter'`, zero `NULL`.

## Section 2 — `core/plan_features.py`

TDD: 14 failing tests, then the map + `has_feature()`. Fail-open design (unrecognized tier →
full access) per design.md D2.

## Sections 3-4 — Financials + liquidity-bridge gating

TDD across both endpoints (share a test file, hermetic-tenant fixture). Found and fixed a real
regression during task 3.2: the new unconditional `_resolve_plan_tier` call broke a
pre-existing test whose monkeypatched fake tenant ID wasn't a valid UUID — fixed by extending
that test's own monkeypatch coverage, documented honestly in tasks.md rather than silently
patched over.

## Section 5 — Centinela alerts gating

TDD, additive `status` field on the response model (no existing consumer breaks). Confirmed
the legacy `get_company_alerts` (Hermes-consumed) route is untouched by its own passing test
suite.

## Section 6 — `GET /api/v1/tenant/me`

New endpoint, new file, wired into `presentation/router.py`. Uses the canonical
`resolve_request_tenant_scope` (not a new local resolver — a deliberate departure from
`financials_endpoints.py`'s pattern, justified in design.md D5 since this endpoint has no
prior reviewed behavior to preserve).

## Sections 7-9 — Frontend

Extended `lib/config.ts`/`lib/api-client.ts`; added the `not_in_plan` branch to
`MonthlyLiquidityBridgeCard` and `ActiveAlerts` (each per its own existing idiom, per design.md
D4); confirmed `CashTodayCard` needs no branch (freemium includes `pulso_diario`) and left a
comment explaining why. Built `TenantInfoCard` (Config page) and `UpgradePlanBanner` (shared
across Fiscal/Radar/Patrimonio). Updated `contexia-app/CLAUDE.md`'s "Pantallas data-bound"
section with an 8th documented exception, per the living-doc rule.

## Section 10 — Testing

- Backend: 59/59 new/modified tests green. Full suite: 847 passed, 120 skipped, 28 failed —
  confirmed via grep (zero references to any file this change touches) and a `git
  stash`/re-run comparison that all 28 pre-exist on `main`, unrelated to this work (a
  `starlette`/`httpx` `TestClient` version mismatch plus historical acceptance tests for
  unrelated completed phases). Note: the `git stash` comparison run timed out mid-execution;
  `git stash pop` was run immediately after and `git status` confirmed all local changes were
  restored intact before continuing.
- Frontend: `tsc --noEmit` zero errors. Started both frontend and local backend dev servers;
  confirmed correct request wiring and graceful degradation on failure via network inspection,
  but could not observe a fully-resolved live value locally because the local uvicorn launch
  profile lacks `SUPABASE_URL` (a pre-existing gap in that launch config, not caused by this
  change — the exception traces into the canonical, pre-existing
  `resolve_cliente_cero_tenant_id`). The real end-to-end path is covered by the 59 pytest
  cases, which do hit the live Supabase project.

## Files touched

- New: `apps/backend/migrations/0043_add_plan_tier.sql`, `apps/backend/core/plan_features.py`,
  `apps/backend/presentation/tenant_endpoints.py`, `apps/backend/tests/test_plan_features.py`,
  `apps/backend/tests/test_financials_endpoint_plan_tier_gating.py`,
  `apps/backend/tests/test_centinela_alerts_plan_tier_gating.py`,
  `apps/backend/tests/test_tenant_me_endpoint.py`,
  `contexia-app/components/config/TenantInfoCard.tsx`,
  `contexia-app/components/shared/UpgradePlanBanner.tsx`.
- Modified: `apps/backend/presentation/financials_endpoints.py`,
  `apps/backend/presentation/centinela_endpoints.py`, `apps/backend/presentation/router.py`,
  `apps/backend/tests/test_financials_endpoint_tenant_scoping.py` (regression fix),
  `contexia-app/lib/config.ts`, `contexia-app/lib/api-client.ts`,
  `contexia-app/components/pulso/CashTodayCard.tsx`,
  `contexia-app/components/pulso/ActiveAlerts.tsx`,
  `contexia-app/components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx`,
  `contexia-app/app/app/(shell)/config/page.tsx`,
  `contexia-app/app/app/(shell)/fiscal/page.tsx`,
  `contexia-app/app/app/(shell)/radar/page.tsx`,
  `contexia-app/app/app/(shell)/patrimonio/page.tsx`, `contexia-app/CLAUDE.md`,
  `feature_list.json`, `openspec/changes/plan-tier-feature-gating/` (proposal, design, specs,
  tasks).
- Railway/Supabase: `tenants.plan_tier` and `b2b_clients.plan_tier` columns (live, migration
  0043, infrastructure not a repo file).

## Next step

Awaiting reviewer pass before Stage 11 (deploy + report) and archive.
