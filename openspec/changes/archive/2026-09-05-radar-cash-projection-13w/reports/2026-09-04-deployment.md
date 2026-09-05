# Deployment report — radar-cash-projection-13w

**Date:** 2026-09-04 (deploys landed 2026-09-05 UTC)
**Change:** Radar de Caja — 13-week cash projection (Module 1 of Pulso Diario v2)
**Deployed by:** Claude Opus 5 session, authorized by the founder

## What shipped

| Surface | What | Where |
|---|---|---|
| Backend | `GET /api/v1/radar/proyeccion-caja` | Railway `antigravity-app-production-175a` |
| Frontend | `CashProjection13wCard` on `/app/radar` | Vercel `contexia.online` |
| Docs | `ARCHITECTURE.md`, `contexia-app/CLAUDE.md` (9th data-bound screen) | repo |

## Commits

| Commit | What |
|---|---|
| `40df84f` | Endpoint + service + PWA card + docs + OpenSpec artifacts |
| `0454f04` | Bump the **live** root `sw.js` `CACHE_VERSION` → `v18-2026-09-04` |
| `0855e13` | **Fix:** mount `proyeccion-caja` at `/radar`, not under `/agents/radar-predictivo` |
| `82d27f6` | **Fix:** sync the static export to the paths Vercel actually serves |

## Verification

- **Backend, live:** `GET https://antigravity-app-production-175a.up.railway.app/api/v1/radar/proyeccion-caja` → **401** without a token (route registered, auth enforced). Railway deployment status `SUCCESS`, `Application startup complete`, `/api/v1/health` → 200.
- **Frontend, live:** `/app/radar` serves the "Radar de Caja — 13 semanas" card (verified with a cache-busted request, since Vercel returns `X-Vercel-Cache: HIT` on this path).
- **Service worker:** `https://contexia.online/sw.js` → `CACHE_VERSION = "v18-2026-09-04"`.
- **Tests:** 16 new, all green. Full backend suite A/B'd against a stash of this change's diff — 33 failed / 924 passed before, 33 failed / 938 passed after. The 33 failures and 3 collection errors are pre-existing and untouched.
- **Browser (pre-deploy, mobile 375×812):** ready / `sin_historico_suficiente` / error / loading states all confirmed against fixtures matching the response contract; two-band confidence split renders; no horizontal scroll.

## Three things that went wrong, and the rules they produced

### 1. The endpoint deployed to the wrong path (404 in production)

`presentation/router.py` mounts `radar_endpoints.router` at `/agents/radar-predictivo`. The new route inherited that prefix, so production answered **404** for the documented `/api/v1/radar/proyeccion-caja`.

**Why the tests missed it:** every endpoint test called `get_cash_projection()` as a plain async function (the `test_agent_stub_endpoints_tenant.py` pattern). That passes no matter where — or whether — the router is mounted.

**Fix:** `radar_endpoints.py` exports a second `pwa_router` carrying only `/proyeccion-caja`, mounted at `/radar`, matching the repo's existing split between the agent surface (`/agents/*`) and the clean per-tenant paths the PWA reads (`/financials`, `/centinela`, `/tenant`).

**Rule earned:** *a new HTTP route needs a test asserting its actual mounted path against `presentation.router.api_router`, not just a direct call to the handler.* Added as `TestRouteRegistration`.

### 2. The static export was synced to a path nothing serves

`vercel.json` sets `"outputDirectory": "."`, and the rewrite `/app/radar → /app/radar.html` resolves against the repo root — so the served file is `app/radar.html`. The sync had been done as `contexia-app/out/*` → `app/`, which produces `app/app/radar.html`: a complete, unreachable shadow copy. The endpoint was live while `/app/radar` still served the old page.

Commit `897a2e7` (2026-09-02, a prior session) had already made the same mistake, which is where the `app/app/` tree came from. The last known-good sync is `270a859`.

**Rule earned:** *the sync target is the repo root — `out/*.html` and `out/_next/` to the root, `out/app/*` to `app/`. Verify by grepping the file the rewrite actually resolves to (`app/radar.html`), never the one the sync happened to write.*

### 3. The live service worker was not the one that got bumped

`contexia-app/public/sw.js` and the synced `app/sw.js` were bumped, but `/sw.js` is served from the **repo root** `sw.js` with no rewrite. Leaving it at v17 would have pinned viewers to the stale cached shell — the exact failure mode CLAUDE.md §9 documents.

**Rule earned:** *the service worker to bump is the repo-root `sw.js` — the one `curl https://contexia.online/sw.js` returns.*

## Blocked / not done

- **4.5 (endpoint p95 < 2s) and 8.3 (Cliente Cero verification against real Shadow GL data)** — both need a backend running against real Supabase credentials, unavailable in this session. Not claimed as done.
- **Adoption tracking** — descoped: `contexia-app` has no analytics pattern to hook into, and adding one is a separate decision (see proposal.md and tasks.md 6.2).

## Concurrent-session note

Another session was committing to `main` throughout this work (HEAD moved from `897a2e7` through several commits). Its uncommitted work — a plan-tier rename ("Pulso Básico"/"GPS Financiero"/"Contexia Total") and Jarvis upsell banners in `TenantInfoCard.tsx`/`UpgradePlanBanner.tsx`/`plan_features.py` — was present in the working tree and had been picked up by the first build. It was stashed, the export rebuilt clean, and the work restored untouched, so **none of it shipped in these commits**. The founder approved this approach explicitly. Some Jarvis strings do appear in production chunks, but those are from files already tracked in `HEAD` before this session — already-shipped work, not introduced here.
