## Summary
- Remove dual-role logic from login.html; each email maps to exactly one role
- New: `growth@contexia.online` = cliente (test account, created in Supabase Auth)
- Existing: `contexia.marketing@gmail.com` = admin
- Delete `/wizard/dashboard/` route (dead code under single-role policy)
- Add Vercel Edge `middleware.ts` gating `/app/*` and `/app-admin/*` with JWT cookie verification (HS256 via Web Crypto API, zero deps)
- Kill `js/auth.js` legacy with hardcoded admin/admin creds + clean 9 HTMLs
- Add `auth_audit` table + endpoint for login attempt logging (fire-and-forget POST)
- Title fix for Bunker Admin shell

Full spec: [`specs/audit-login-2026-05-25.md`](specs/audit-login-2026-05-25.md)

## Closes
- P0-1 (legacy js/auth.js)
- P0-3 (logout cleanup)
- P0-5 (dual-role toggle bug)
- P1-1 (dead /wizard/dashboard/)
- P1-4 (audit logging)
- Partially: P0-2 (middleware code done, gated on env var)

## Pre-deploy requirements
- [ ] Set env var `SUPABASE_JWT_SECRET` in Vercel project `contexia-web-app` (value from Supabase project `kpynymwghfwshvcvevxq` → Settings → API → JWT Secret). Until set, middleware fail-opens with a console warning — not a security regression, just no gate.
- [ ] Run migration `contexia-wizard/supabase/migrations/20260525_create_auth_audit.sql` in Supabase project `wzqymuzpjbagnbgsiqig` (the wizard project — NOT the auth project). Until run, audit POSTs return 500 silently (login still works).
- [ ] After confirming `SUPABASE_JWT_SECRET` set, flip `middleware.ts:96` from `console.warn` fail-open to `return Response.redirect(loginUrl, 302)` fail-closed.

## Out of scope (follow-up tickets)
- **P0-2 hardening**: token refresh cookie sync (currently users get bounced to login every ~1h).
- **P0-4**: consolidate `ADMIN_EMAILS`/`CLIENT_EMAILS` from `login.html` + `app-admin/index.html` to Supabase `app_metadata.role` (eliminates 2 remaining hardcoded lists).
- **P0-6**: kill `app.contexia.online` Vercel project (T11-T16 in spec, manual).
- **P1-2**: clean orphan `_next/static/chunks/*.js` bundles in root.
- **P1-3**: dedicated OAuth callback route.

## Test plan
- [ ] After SUPABASE_JWT_SECRET + migration land: open `contexia.online`, click "Acceso App", log in as `growth@contexia.online` → lands on `/app/overview` (modern dark PWA, not legacy green)
- [ ] Log out, log in as `contexia.marketing@gmail.com` → lands on `/app/bunker` (Bunker Admin shell)
- [ ] With session active, direct URL to `/app/bunker` as cliente → bounces to `/app/overview`
- [ ] Direct URL to `/app/bunker` without session → bounces to `/login.html?next=/app/bunker`
- [ ] Check `auth_audit` table has 1 row per attempt (success + failure paths)
- [ ] Verify `/wizard/` Shadow Audit still loads (not collateral damage)
- [ ] Verify Google + Microsoft SSO buttons still work end-to-end

🤖 Generated with [Claude Code](https://claude.com/claude-code)
