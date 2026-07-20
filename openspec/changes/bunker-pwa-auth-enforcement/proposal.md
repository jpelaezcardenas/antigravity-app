## Why

**Corrected scope (superseding an earlier, wrong-premise draft of this proposal)**: a real,
already-working authentication system exists for the Búnker/PWA — `login.html` (root of the repo)
authenticates via **Supabase Auth** (`client.auth.signInWithPassword`), and `middleware.ts` (Vercel
Edge) already gates every `/app/*` and `/app-admin/*` page server-side against the resulting
Supabase-issued JWT (role-aware: `/app/bunker` requires `app_metadata.role=admin`). Both accounts
the founder needs already exist in `auth.users` with correct roles
(`contexia.marketing@gmail.com` → admin, `growth@contexia.online` → cliente) — **no account
provisioning is needed at all**.

The real, still-open gap: `login.html` already stores the Supabase access token in
`localStorage["token"]`, but the frontend's data-bound API clients (`lib/api-client.ts`,
`lib/social-ops-api.ts`, `lib/crm-api.ts`, `lib/sell-machine-api.ts`) never read it or send it —
every request to the Railway backend goes out with no `Authorization` header at all. And the
backend's `get_current_user`/`AUTH_ENFORCED` mechanism only recognizes the backend's own
custom-signed JWT (`JWT_SECRET`), not the Supabase-issued one `middleware.ts` already validates
(`SUPABASE_JWT_SECRET`) — the two token schemes don't interoperate. `middleware.ts` protects page
navigation on Vercel, but every data-bound fetch call goes **directly to Railway**
(`https://antigravity-app-production-175a.up.railway.app`), bypassing Vercel (and its middleware)
entirely — so the backend API itself remains unauthenticated regardless of the frontend gate.

## What Changes

- Frontend: a shared `authenticated-fetch.ts` helper attaches
  `Authorization: Bearer <localStorage["token"]>` (the Supabase access token `login.html` already
  stores there) to every data-bound fetch; all 4 API clients route through it.
- Backend: `core/deps.py`'s `get_current_user` also accepts a Supabase-issued JWT (verified against
  `SUPABASE_JWT_SECRET`, same algorithm/verification `middleware.ts` already performs), as a
  fallback when the backend's own `verify_token` doesn't recognize it.
- Backend: `Depends(get_current_user)` added to `crm_endpoints.py`, `social_ops_endpoints.py`
  (router-level — confirmed no external/machine caller depends on either), and to the
  Búnker-human-facing endpoints only in `sell_machine_endpoints.py` (leaving the Hermes↔backend
  machine-to-machine bridge endpoints unguarded — see design.md Decision 6).
- Staged rollout unchanged in spirit: verify with a real session before flipping
  `AUTH_ENFORCED=true`.
- **Explicitly NOT building**: a new login page, a new JWT scheme, a registration endpoint, or a
  client-side route guard (page-level gating is already handled server-side by `middleware.ts`,
  stronger than anything client-side could add).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
(no `openspec/specs/` capability document currently describes auth on these screens; this closes
accepted risk R1 from `crm-b2c-sell-machine-cockpit`/`sell-machine-creative-swarm`.)

## Impact

- **Backend**: `core/deps.py` (Supabase-JWT fallback), `config.py` (`SUPABASE_JWT_SECRET`
  declared), `presentation/crm_endpoints.py`, `presentation/sell_machine_endpoints.py`,
  `presentation/social_ops_endpoints.py`.
- **Frontend**: `lib/authenticated-fetch.ts` (new, minimal — just attaches the header, no login
  page/guard logic), the 4 `lib/*-api.ts` clients.
- No migration. No new accounts. No new login UI.
