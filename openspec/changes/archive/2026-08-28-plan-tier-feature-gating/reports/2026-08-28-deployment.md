# Stage 11 deployment report — plan-tier-feature-gating

- Date: 2026-08-28
- Commit: `23d8cbb` (`feat: enforce plan_tier feature gating on freemium onboarding path`)

## Migration

Applied live to Supabase project `kpynymwghfwshvcvevxq` **before** the code deploy (migration
0043, via Supabase MCP `apply_migration`) — additive-only (`ADD COLUMN IF NOT EXISTS` + a guarded
`CHECK` constraint), so it was safe to apply ahead of the endpoint changes that depend on it.
Verified: 13/13 `tenants` rows and 10/10 `b2b_clients` rows landed on `plan_tier = 'starter'`,
zero `NULL`, zero unexpected values.

## Backend (Railway `production-175a`)

- Pushed to `main` → Railway auto-deployed. Deployment `31b84b6b-c7d2-4fef-8535-d09be284306f`:
  `SUCCESS`.
- Immediately post-deploy, `GET /api/v1/health` returned a `502` — the documented ~80s cold-start
  window (ARCHITECTURE.md "arranque ~80s antes de servir"), not a regression. Re-checked with a
  bounded polling loop (5s interval, capped at 15 attempts): healthy after ~50s
  (`{"status":"healthy",...}`).
- Verified live: `GET /api/v1/tenant/me`, `GET /api/v1/financials`, and
  `GET /api/v1/centinela/alerts` all return `{"detail":"Invalid or missing authentication
  token"}` when called with no `Authorization` header — consistent, correct behavior across all
  three (production runs with `AUTH_ENFORCED=True`, unlike local dev's permissive staging
  identity). This confirms the new endpoint's `Depends(get_current_user)` wiring works
  identically to its siblings, with no accidental auth bypass introduced.

## Frontend (Vercel)

- Deployment `dpl_3oCdeV64ZoaVz1KcyTbiamrXu31x` (commit `23d8cbb`): `state: "READY"`,
  `target: "production"`.

## What was NOT verified live (founder action, same deferred pattern as prior changes)

A real, authenticated client session exercising the resolved-tenant path (Config showing a real
`legal_name`/`plan_tier`, the freemium upgrade banner appearing for an actual `freemium`-tier
tenant) requires logging in as a real provisioned client — this agent does not handle plaintext
credentials. This is the same deferred-verification pattern already established for several prior
changes in this repo (e.g. `taty-per-tenant-profiles` 11.6/11.6b, `pwa-tenant-aware-screens`
13.6). The correctness of the resolved-tenant path is instead covered by 59 passing pytest cases
against the live Supabase project (Section 10 of `tasks.md`), independently re-run and confirmed
by the reviewer.

**FOUNDER ACTION (not blocking, deferred per the established pattern above):** log in as a real
provisioned B2B client and confirm the Config page shows the real company name and tier, and
(optionally) flip one test tenant's `plan_tier` to `'freemium'` to visually confirm the upgrade
banner appears on Fiscal/Radar/Patrimonio and the Centinela-alerts/liquidity-bridge "not in your
plan" states render correctly.

## Conclusion

All 33 changed/added files committed and pushed. Both deploy targets (Railway backend, Vercel
frontend) green. Migration applied and verified live. Auth wiring on the new endpoint verified
consistent with existing endpoints. Ready to archive.
