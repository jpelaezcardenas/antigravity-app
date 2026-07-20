# Step 4 verification — bunker-pwa-auth-enforcement (corrected scope)

Date: 2026-07-20

## Course correction (documented for the record)

An earlier draft of this change built a parallel login page, a custom `POST /auth/register`
endpoint, and a client-side route guard — all against the backend's own homegrown JWT scheme.
The founder asked why an account with his email already existed, which surfaced a real,
already-working system this work had been built blind to: `login.html` (Supabase Auth) +
`middleware.ts` (Vercel Edge, verifies the Supabase JWT server-side, role-aware). Both accounts
needed (`contexia.marketing@gmail.com`→admin, `growth@contexia.online`→cliente) already existed
in `auth.users`, confirmed via direct SQL, created 2026-05-22/25 — long before this session. All
wrong-premise work was reverted (login page, register endpoint, route-guard hook/component,
custom-JWT backend changes) before continuing.

## Backend test results

64/64 green, zero regression:

```
tests/test_auth_deps.py ............... (15, incl. 5 new Supabase-JWT-fallback tests)
tests/test_auth_service.py
tests/test_crm_service_b2c_logic.py
tests/test_crm_b2c_endpoints.py
tests/test_sell_machine_endpoints.py
tests/test_social_ops_endpoints.py
tests/test_social_ops_service.py
```

## Scope of the corrected change

- **Backend**: `config.py` (`SUPABASE_JWT_SECRET` declared — already set in Railway, never
  declared as a `Settings` field before), `core/deps.py` (`_verify_supabase_token` fallback in
  `get_current_user`, tried after the backend's own `verify_token` fails), plus the
  `Depends(get_current_user)` additions on `crm_endpoints.py`/`social_ops_endpoints.py`
  (router-level) and `sell_machine_endpoints.py` (per-endpoint, Búnker-facing only — Hermes bridge
  left unguarded), and the `bcrypt<4.1` pin — all unchanged from the earlier draft, still correct
  regardless of which token scheme `get_current_user` accepts.
- **Frontend**: `lib/authenticated-fetch.ts` rebuilt minimal (just attaches the header — no
  redirect/session-clear logic, since `middleware.ts` already owns that server-side); the 4
  `lib/*-api.ts` clients' wiring through it (unchanged from the earlier draft — this part was
  always correct).
- **Removed** (wrong premise): `app/login/page.tsx`, `lib/use-require-auth.ts`,
  `components/layout/RequireAuthGuard.tsx`, the `POST /auth/register` endpoint and its tests, the
  `useRequireAuth()` wiring in `/app/bunker` and the shell layout.

## Frontend build

`npm run build` (after clearing a stale `.next` type-cache referencing the deleted `/login` page):
compiled successfully, TypeScript clean, 12 routes generated (back to the original route set — no
stray `/login`).

## Still pending before Stage 11's flag flip

`AUTH_ENFORCED` stays `False` until a real Supabase-authenticated session (via the existing,
unmodified `login.html`, using the founder's own credentials) is confirmed working end-to-end
against each of the five data-bound screens.
