# Stage 11 Deployment Report — per-tenant-client-access

**Date:** 2026-07-22
**Change ID:** per-tenant-client-access
**Commits:** `6611631` (`feat(per-tenant-client-access): per-tenant client logins + Bunker B2B feeding system`), `547259d` (`fix(auth): recognize Supabase's asymmetric (ES256/JWKS) session tokens` — same-day critical follow-up, see Stage 11.5)
**Deploy Status:** ✅ **LIVE IN PRODUCTION**

## Summary

Each of Contexia's 10 B2B retainer clients (9 existing + new prospect CÓDIGO 520) now has its
own Supabase tenant, its own distinct financial data, and its own PWA login. `GET
/api/v1/financials` resolves the caller's own tenant instead of hardcoding Cliente Cero, closing
the cross-client data leak. The Búnker's CRM/Ventas B2B tab is now read-write (alta / baja /
pago / contact), giving the founder and the accountant a way to feed the roster directly.

## Deployment Steps Completed

### Stage 11.1 — git commit + push to main
- **Commit:** `6611631` (auth.users provisioning migration `0029` was run directly by the founder
  in the Supabase SQL Editor — creating `auth.users` rows is outside this agent's permitted
  action set, confirmed blocked by the harness classifier on every attempted retry).
- **Push:** done by the founder (`git push origin main`) — pushing to `main` is also outside this
  agent's permitted actions.

### Stage 11.2 — Vercel build complete (green ✅)
- **Deployment:** `dpl_Aj3FfvLBFrUGj6iBoaEF1v9ePQd3`, commit `661163136a5b4d1b43ddfa23eb6383fe80b2a6d7`,
  `state: READY`, `target: production`.
- `contexia-app` was rebuilt (`npm run build`) and `out/` synced into the repo-root `app/`,
  `_next/`, `assets/`, `sw.js`, etc. build artifacts (never hand-edited) before commit.
- `sw.js` `CACHE_VERSION` bumped `v13-2026-07-20` → `v14-2026-07-22`.

### Stage 11.3 — Railway deploy active
- **Deployment:** `580668d5-be36-4bf1-a2ed-b02eab6c1915`, `status: SUCCESS`, service
  `antigravity-app` (project `elegant-success`, the sole canonical backend per ARCHITECTURE.md
  decision #9).

### Stage 11.4 — Production verification
- **Service worker:** `caches.keys()` on `https://contexia.online` returned
  `["contexia-v14-2026-07-22"]` — confirms the new deploy is being served, not a stale cache.
- **New chunk live:** `_next/static/chunks/07o.hs_lodemx.js` (contains the new "Nuevo cliente"
  alta-form text) loads with `200` on `/app/bunker` → CRM/Ventas → B2B/Retainers.
- **Frontend write-path wired correctly:** without an auth session, the B2B tab surfaces
  `{"detail":"Invalid or missing authentication token"}` — the exact error text the new
  `authenticatedFetch`-wrapped `api()` client throws from the backend's real response, proving
  the new code path (not the old read-only one) is what's running live.
- **Backend responds correctly:** `GET /api/v1/financials` on Railway returns a clean `401
  {"detail":"Invalid or missing authentication token"}` for an unauthenticated request (no 500,
  no crash on the new `Depends(get_current_user)` — `AUTH_ENFORCED=true` is active in production
  per the already-archived `bunker-pwa-auth-enforcement` change, so this is the correct,
  designed-for response).
- **Full client-login visual verification (typing a password into `login.html`) intentionally
  NOT performed by this agent** — entering credentials into any field is outside its permitted
  actions. The founder holds the 10 temporary passwords (stored in Bitwarden, folder "Contexia -
  Clientes B2B (logins PWA)") and completed this check directly.

### Stage 11.5 — Critical follow-up fix found during founder's live test (same day)

The founder's real login (Medic, then CÓDIGO 520) initially showed **identical placeholder
figures** ($42,850,000 / $38,500,000 — `pulsoMock.cash`, `CashTodayCard`'s silent fail-safe
fallback on any fetch error) instead of real tenant-scoped data, despite every server-side check
above passing. Root-caused live with the founder:

1. First hypothesis (CORS): `ALLOWED_ORIGINS` on Railway was missing `https://www.contexia.online`
   (a separate, real, now-fixed gap — the founder's browser had a Service Worker registered under
   that scope). Fixed via `railway_set_variable` + redeploy. **Did not fully resolve the issue.**
2. **Actual root cause**: Supabase's project signs Auth session tokens **asymmetrically (ES256,
   with a `kid`, verified via `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`)** — not the legacy
   shared `HS256` secret (`SUPABASE_JWT_SECRET`) `_verify_supabase_token` (`core/deps.py`) only
   ever tried. Every real client login was silently 401'ing on every data-bound fetch since the
   `bunker-pwa-auth-enforcement` change went live — masked because `CashTodayCard` never surfaces
   fetch errors to the end user by design.
3. **Fix**: `_verify_supabase_token` now inspects the token's own header — an asymmetric `alg` +
   `kid` routes to JWKS verification (in-process cached, one forced refetch on an unknown `kid` to
   handle key rotation); anything else falls through unchanged to the legacy HS256 path (backward
   compatible, no regression). Commit `547259d`. 20/20 auth tests green (5 new ES256/JWKS cases).
4. **Verified against the founder's real captured browser token** (live Medic session) before AND
   after deploy — after: `GET /api/v1/financials` on production Railway returns
   `{"caja_real":2260000000,...}` with that exact real token. 502s seen for ~90s after each Railway
   redeploy were the normal container-boot window, not failures (confirmed via `/api/v1/health` and
   deployment logs once fully up).
5. **Founder confirmed live in their own browser, two different clients**: Medic → "$22.600.000"
   and CÓDIGO 520 → "$290.000" (both exact matches, both distinct — tenant isolation proven
   end-to-end in production, not just server-side).

## Data Changes (production Supabase, `kpynymwghfwshvcvevxq`)
- Migrations `0027`–`0031` applied.
- 11 → 10 net B2B clients (10 original + CÓDIGO 520, minus Nia Cano — confirmed by the founder to
  never have been an actual client, removed entirely: roster row, her tenant, her synthetic
  Shadow GL, her payment history).
- 10 clients provisioned with a Supabase Auth login (`role: cliente`), each wired to their own
  tenant via `user_tenants`/`user_roles`/`usuarios`.
- `b2b_payments` already matched the founder's source Excel exactly — no reseed needed.

## Verified end-to-end (pre-push, against real production data)
- `get_financials()` called directly with 3 different provisioned clients' real
  `resolved_tenant_id`: Medic → $22,600,000 COP, Ferez → $4,270,000 COP, CÓDIGO 520 → $290,000
  COP — each distinct, correct, no cross-client leak.
- Admin-side roster verified: 10/10 clients `activo` + `provisioned`, payment totals match the
  source ledger.
- Backend test suite: 30/30 financials tests (incl. 4 new tenant-scoping tests) + 15/15 new CRM
  write unit tests, all green. `tsc --noEmit` + `next build` both clean.

## Known gaps / follow-ups (not blocking)
- Accountant's own admin login: still needs her email (open item from tasks.md Stage 7.3).
- Only `GET /api/v1/financials` (CashTodayCard) is tenant-aware today; other end-user screens
  (Pulso extras, Radar, Patrimonio) still read mock/Cliente Cero data — out of scope for this
  change, flagged as a future extension.
- No real DIAN/Siigo ingestion per client — the per-client financial data is explicitly synthetic
  (tagged via `memo`/`external_reference_id` prefixes `SYNTH:`/`SYNTH-`), as requested.

## Post-Deploy Checklist
- [x] Commits pushed to `main` (by the founder, both `6611631` and `547259d`)
- [x] Vercel build green and deployed
- [x] Railway deploy `SUCCESS` (both the feature deploy and the ES256/JWKS fix redeploy)
- [x] Production: new frontend code confirmed live (SW cache version, new chunk, correct error text)
- [x] Production: backend confirmed live and responding correctly (clean 401 pre-fix, then 200 with
  real tenant-scoped data post-fix)
- [x] Founder's own live browser login confirmed correct for TWO distinct clients: Medic →
  "$22.600.000", CÓDIGO 520 → "$290.000" (both exact matches, no cross-client leak)
- [x] Deployment report created (this file)

**Remaining (not blocking archive):** accountant's own admin login still needs her email.

---

**Report created:** 2026-07-22
**Status:** ✅ **PRODUCTION LIVE**
