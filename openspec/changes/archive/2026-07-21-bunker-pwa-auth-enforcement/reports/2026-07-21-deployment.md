# Deployment report — bunker-pwa-auth-enforcement

Date: 2026-07-21

## Summary

`AUTH_ENFORCED=true` is now genuinely live in production. Every data-bound backend route
(`/api/v1/crm/*`, `/api/v1/sell-machine/*` Búnker-facing endpoints, `/api/v1/social-ops/*`) now
requires a valid session — either the backend's own JWT or a real Supabase Auth session token
(the one `login.html` already issues). This closes risk R1 from the original
`crm-b2c-sell-machine-cockpit`/`sell-machine-creative-swarm` plan, verified end-to-end with a real
production login, not just unit tests.

## The corrected journey (for the record)

This change went through a real course-correction mid-implementation, documented here because it's
instructive:

1. **First attempt (wrong premise, fully reverted)**: built a parallel login page, a custom
   `POST /auth/register` endpoint, a client-side route guard, and a custom JWT scheme — all before
   discovering a real, already-working authentication system existed (`login.html` + Supabase
   Auth + `middleware.ts`, built in an earlier session, confirmed via git history and live
   `auth.users` rows dated May 2026). Reverted entirely once discovered.
2. **Corrected implementation**: `core/deps.py`'s `get_current_user` extended with a
   `_verify_supabase_token` fallback (`SUPABASE_JWT_SECRET`, matching `middleware.ts`'s own
   verification), and a minimal `authenticated-fetch.ts` that attaches the Supabase token
   `login.html` already stores in `localStorage["token"]` — no new login UI needed.
3. **A real, pre-existing dependency bug found and fixed**: `bcrypt>=4.1` breaks
   `passlib==1.7.4`'s hash/verify calls (`AttributeError: module 'bcrypt' has no attribute
   '__about__'`) — pinned `bcrypt<4.1` in `requirements.txt`. This could have been silently
   breaking real password verification in production independent of this change's own scope.
4. **Addendum, at the founder's request**: removed "Sign in with Microsoft" from `login.html`
   (Google-only SSO), wired real self-service sign-up (`client.auth.signUp`) and a real
   "Forgot password?" flow (`resetPasswordForEmail` + new `reset-password.html` completion page),
   and added a `set_default_role_on_signup` Postgres trigger so self-service sign-ups always
   default to `role: cliente` — never `admin`, which stays a manual `UPDATE` (same pattern as the
   existing `20260525_seed_user_roles.sql` precedent).
5. **Real Google OAuth end-to-end verification**: Google was already enabled as a Supabase Auth
   provider (done by the founder + Manus, an external agent, in Google Cloud Console + Supabase
   Dashboard — confirmed via a handoff report, cross-checked against the live database rather than
   trusted blindly). Two real dashboard misconfigurations were found live during testing and fixed
   by the founder directly (an agent cannot touch Supabase Auth dashboard settings or OAuth
   secrets): the Site URL was still `http://localhost:3000` (breaking password-reset email
   redirects), and the Google provider's Client Secret hadn't actually persisted despite an earlier
   report claiming it had. After both fixes, `jpelaezcardenas@gmail.com` signed in via Google for
   real, auto-creating its `auth.users` row with `role: cliente` (via the new trigger), then
   promoted to `role: admin` via a single `UPDATE` (not account creation — a role-flag change on an
   already-real, already-authenticated account).

## Stage 11 — the flag flip

Flipping `AUTH_ENFORCED=true` via `railway_set_variable` did **not** trigger an automatic redeploy
— confirmed live (`GET /crm/b2b/clients` with no token still returned `200` after the flag was
set). This is because `pydantic-settings`'s `Settings()` object is instantiated once at process
startup; Railway doesn't restart a running service on a var-only change for this project. A manual
redeploy (`railway_redeploy`) was required. After that redeploy (`621db198`, `SUCCESS`):

- `GET /api/v1/health` → `200` (public endpoint, unaffected, confirms the deploy itself is healthy).
- `GET /api/v1/crm/b2b/clients` with no `Authorization` header → `401` (previously `200` via the
  permissive staging fallback) — **enforcement confirmed genuinely active**, not just configured.

## Verification evidence

- 64/64 backend tests green (Section 4 of tasks.md), zero regression.
- `npm run build` clean, no leftover files from the reverted wrong-premise draft.
- Real production Google OAuth sign-in verified end-to-end, including a real Postgres trigger
  firing correctly (`set_default_role_on_signup`) and a real role promotion.
- Real data-bound screens (CRM/Ventas, Sell Machine) confirmed loading correctly by the founder
  while authenticated with the real session.
- Enforcement itself confirmed live via a real unauthenticated request returning `401` post-deploy.

## Accepted risks / limitations (carried from design.md)

- No role/authorization model inside the FastAPI backend itself — `middleware.ts` gates Búnker
  page navigation by role; backend routes only assert "authenticated," not "admin." Flagged as a
  future decision, not built here.
- Hermes↔backend machine-to-machine endpoints (`/tasks/*`, `/campaigns/{id}/dispatch`,
  `/creative-loop/run`, `/telemetry/report`) remain unguarded by design — Hermes has no browser
  session. Their own authentication (e.g. a shared API key) is a separate future decision.
- Supabase's built-in email rate limit was hit during live testing (unrelated to this change's
  code) — resolves on its own after ~1 hour, or permanently via configuring custom SMTP (the
  founder's own action, requires his own SMTP provider credentials).
