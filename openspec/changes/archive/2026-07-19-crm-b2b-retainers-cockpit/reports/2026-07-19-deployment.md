# Deployment Report — crm-b2b-retainers-cockpit

**Date:** 2026-07-19

## What shipped

Replaced the Búnker's static-mock "CRM / Ventas" section with a live B2B retainer cockpit:

1. **Data model**: `b2b_clients` + `b2b_payments` (normalized ledger, one row per client per
   month), tenant-scoped to Cliente Cero, admin-only RLS on the live `role_type` enum
   (migrations `0020`, `0021`).
2. **Seed**: Contexia's 10 real B2B retainer clients, Jan–Jun 2026 monthly payments migrated from
   the manual Excel — correcting a source-data typo (Repuestos Don Álvaro's March amount is
   1,200,000 COP, not the pasted 12,000,000).
3. **Backend**: `GET /api/v1/crm/b2b/clients`, `GET /api/v1/crm/b2b/payments` (server-pivoted
   grid + totals), Supabase-preferred/demo-fallback, behind a new `CRM_CANONICAL` feature flag.
4. **Frontend**: `CrmVentasSection.tsx` rewritten as a tab shell ("B2B / Retainers" live,
   "B2C / Renta Natural" placeholder for a later change); new `lib/crm-api.ts` +
   `components/bunker/crm/B2bRetainersTab.tsx`, cloning the Social Content Ops data-bound idiom.
5. **Docs**: `contexia-app/CLAUDE.md` documents this as the fourth data-bound exception (after
   CashTodayCard, Social Content Ops, and a concurrently-shipped Onboarding section).

## Commits

- `600a11d` — feat(crm): B2B retainer cockpit backend + OpenSpec artifacts (WIP)
- `963f0df` — test(crm): fix endpoint tests for httpx/starlette TestClient incompatibility
- `1df3c59` — feat(crm): B2B retainers cockpit frontend (tab shell + live grid)
- `62acefb` — docs(crm): document CRM/Ventas B2B as third data-bound screen
- `9cbc520` — test(crm): verification pass (Sections 8-9)
- `1783df7` — Merge branch 'feature/crm-b2b-retainers-cockpit' (resolved `CLAUDE.md` conflict)
- `b8dd433` — chore(pwa): bump service worker CACHE_VERSION (v9→v10)
- `f26dfa4` — chore(bunker): sync contexia-app build output for CRM cockpit + sw.js bump
- `9658b68` — fix(bunker): add missing chunk `188-e0~0ya.2n.js` (404 hotfix)

## Verification performed

- **Tests**: 11/11 runnable backend tests green (credential-free pivot/aggregation logic +
  mocked endpoint-shape/flag-gating tests). Two Supabase-hitting integration suites
  (`test_crm_b2b_schema.py`, `test_crm_service.py`) require `SUPABASE_SERVICE_ROLE_KEY`, absent
  from this machine's local `.env` — same gating convention as `test_shadow_gl_schema.py`; not run
  locally, not required for correctness (verified via direct SQL + production instead).
- **DB**: verified live via Supabase MCP — 10 clients, 60 payment rows, RLS enabled with policies
  present, idempotent (seed re-applied twice, counts/total unchanged).
- **Build**: `tsc --noEmit` clean, `npm run build` green throughout.
- **Production — Vercel**: `https://contexia.online/app/bunker` — CRM/Ventas renders the tab shell;
  all 6 sidebar sections unaffected.
- **Production — Railway** (post flag-flip): `GET /api/v1/crm/b2b/clients` →
  `{"source":"supabase","items":[...10 clients...]}`; `GET /api/v1/crm/b2b/payments` →
  `{"source":"supabase", "totals":{"grand_total":3732000000, ...}}`.
- **Production — full UI**: the live B2B grid renders exactly matching the seed fixture — every
  client, every month, correct amounts (including the corrected Repuestos Don Álvaro March value),
  grand total `$37.320.000`.

## Incidents during this deployment (documented for transparency)

1. **Concurrent session collision**: mid-implementation, another active session/process on this
   same (non-worktree-isolated) machine switched branches, reset, and cherry-picked on top of this
   work. No permanent loss occurred — the concurrent process had stashed the tracked-file diff
   first, and untracked new files survived what appears to have been a transient race. Recovered
   by re-checking out the feature branch, reapplying the relevant stash, and committing early and
   often from that point forward. One further, smaller instance of the same class of collision
   reverted an uncommitted `sw.js` edit shortly after; redone and committed immediately.
2. **Missing-chunk production hotfix**: the additive build-artifact sync's chunk-reference
   verification used a regex that didn't account for `~` in filenames, silently skipping one
   real reference. This chunk 404'd on the first production check. Root-caused, fixed with a
   proper parser (re-verified 0 missing references across all 11 real refs), hotfixed, and
   re-verified clean within the same deployment window.

## Accepted risk (per design.md Risk R1)

`/api/v1/crm/*` endpoints carry no per-request auth beyond the Vercel edge middleware's admin gate
on the `/app/bunker` route and the `CRM_CANONICAL` feature flag — the same posture already accepted
for Social Content Ops. B2B revenue data is more sensitive than social-ops demo data; recommend a
follow-up to add request-level auth (e.g. `AUTH_ENFORCED`) to CRM routes before this surface grows
further (e.g. before Change B's B2C Kanban / payment-approval endpoints ship).

## Known follow-ups (not in this change's scope)

- B2C Kanban funnel (`crm_leads`/`crm_tax_profiles`/`crm_wompi_transactions`) — separate OpenSpec
  change `crm-b2c-sell-machine-cockpit`.
- Write endpoints (edit a payment, toggle client status) — deferred; the read-only grid delivers
  the core value (visibility) already.
- R1 above (request-level auth on CRM endpoints).
