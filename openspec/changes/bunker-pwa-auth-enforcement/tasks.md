## 1. Setup + verification (corrected scope)

- [x] 1.1 Created branch `feature/bunker-pwa-auth-enforcement`.
- [x] 1.2 **Course correction, mid-implementation**: the founder asked why an account with his
      email already existed, revealing a real, already-working auth system (`login.html` +
      Supabase Auth + `middleware.ts`) this change had been built blind to. Reverted the
      wrong-premise work (custom login page, `POST /auth/register` endpoint, client-side route
      guard, custom-JWT wiring) and re-verified from scratch: read `login.html` and `middleware.ts`
      directly, confirmed via live SQL that both needed accounts already exist in `auth.users`
      with correct roles (`contexia.marketing@gmail.com`→admin, `growth@contexia.online`→cliente),
      confirmed `localStorage["token"]` already holds the Supabase access token, confirmed
      `SUPABASE_JWT_SECRET` is already set in Railway but never declared in `Settings`. Kept the
      `bcrypt<4.1` fix (unrelated, still a real bug) and the router-level
      `Depends(get_current_user)` additions on `crm_endpoints.py`/`social_ops_endpoints.py` and the
      per-endpoint additions on `sell_machine_endpoints.py` (all still correct regardless of which
      token scheme `get_current_user` accepts).

## 2. Backend — Supabase-JWT fallback in get_current_user — TDD

- [x] 2.1 Wrote failing tests for `get_current_user`: a Supabase-issued JWT (signed with
      `SUPABASE_JWT_SECRET`, `aud=authenticated`, `sub`/`email`/`app_metadata.role` claims) is
      accepted and resolved; the backend's own JWT still works unchanged; a token signed with the
      wrong secret is still rejected when `AUTH_ENFORCED=True`; an unconfigured
      `SUPABASE_JWT_SECRET` doesn't crash. Confirmed failing.
- [x] 2.2 Declared `SUPABASE_JWT_SECRET` in `config.py`. Implemented `_verify_supabase_token` +
      the fallback in `core/deps.py`'s `get_current_user` (tries the backend's own `verify_token`
      first, then Supabase-JWT decode).
- [x] 2.3 15/15 green in `test_auth_deps.py` (5 new + 10 pre-existing), zero regression.

## 3. Frontend — minimal authenticated-fetch — manual verify

- [x] 3.1 Rebuilt `contexia-app/lib/authenticated-fetch.ts`, minimal: attaches
      `Authorization: Bearer` from `localStorage["token"]`; no redirect/clear-session logic.
- [x] 3.2 Confirmed the 4 data-bound API clients' wiring through it was preserved from before the
      revert (still correct, untouched by the course-correction).
- [x] 3.3 `npm run build` (after clearing a stale `.next` type-cache referencing the deleted
      `/login` page) — clean compile, 12 routes, no leftover login/guard files.

## 4. Verify + DB state (MANDATORY before Stage 11)

- [x] 4.1 Ran the full backend targeted suite: 64/64 green across
      `test_auth_deps.py`/`test_auth_service.py`/`test_crm_service_b2c_logic.py`/
      `test_crm_b2c_endpoints.py`/`test_sell_machine_endpoints.py`/`test_social_ops_endpoints.py`/
      `test_social_ops_service.py`, zero regression.
- [x] 4.2 Wrote `openspec/changes/bunker-pwa-auth-enforcement/reports/2026-07-20-step4-verification.md`.

## 5. Stage 11 — Deploy to Production (MANDATORY, staged rollout)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 5.1 Commit + merge to `main` (check for divergence) + push. Deploy Railway (backend) +
      Vercel (frontend, rebuilt contexia-app + resynced `app/` build artifact). Bump `sw.js`
      CACHE_VERSION.
- [ ] 5.2 Confirm both deploys green. `AUTH_ENFORCED` still `False` at this point.
- [ ] 5.3 **Founder action**: log in for real at the real `login.html` (existing, unmodified) with
      an existing account, confirm each data-bound screen (Caja Real, Social Ops, Onboarding, CRM
      B2B+B2C, Sell Machine) still loads correctly with the real session's token now attached.
- [ ] 5.4 **Only after 5.3 passes**: flip `AUTH_ENFORCED=true` in Railway, confirm the deploy stays
      green, re-verify all five screens once more (confirms enforcement doesn't break the real
      session, and a request with no token now correctly gets rejected).
- [ ] 5.5 Create deployment report at
      `openspec/changes/bunker-pwa-auth-enforcement/reports/YYYY-MM-DD-deployment.md`.

## 6. Archive

- [ ] 6.1 Sync the new `bunker-pwa-auth` capability spec into `openspec/specs/`, archive via
      `git mv` once Stage 11 (including the flag flip) is confirmed complete.
