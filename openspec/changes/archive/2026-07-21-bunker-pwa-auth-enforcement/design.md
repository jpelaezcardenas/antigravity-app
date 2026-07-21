## Context (corrected — supersedes an earlier wrong-premise draft)

An earlier draft of this change built a parallel login page, a custom `POST /api/v1/auth/register`
endpoint, and a client-side route guard — all against the backend's own homegrown `usuarios` table
+ custom JWT (`core/security.py`'s `create_access_token`/`JWT_SECRET`). This was based on an
incomplete picture: a real, already-working, already-deployed authentication system exists
(`login.html` + Supabase Auth + `middleware.ts`), discovered only after the founder asked why an
account with his email already existed. That earlier work has been reverted; this design reflects
the corrected understanding, verified directly against the live system rather than assumed:

- `login.html` (repo root) calls `client.auth.signInWithPassword` against the **same Supabase
  project** the rest of this repo uses (`kpynymwghfwshvcvevxq`), storing the resulting Supabase
  access token in **`localStorage["token"]`** and a `sb-access-token` cookie, plus role/user info
  in `localStorage["cx_user"]`.
- `middleware.ts` (Vercel Edge, repo root) verifies that cookie's JWT (HS256, `SUPABASE_JWT_SECRET`,
  verified via Web Crypto — no npm deps) on every `/app/*`/`/app-admin/*` navigation, redirecting to
  `/login.html` if missing/invalid/expired, and additionally requires `app_metadata.role=admin` for
  `/app/bunker`/`/app-admin/*`. This is real, working, server-side page-level protection —
  confirmed by reading the file directly, not assumed.
- Both accounts the founder needs already exist in Supabase Auth's `auth.users`
  (confirmed via direct SQL against the live database): `contexia.marketing@gmail.com`
  (`role: admin`) and `growth@contexia.online` (`role: cliente`), both created 2026-05-22/25 — long
  before this session. **No account provisioning is needed.**
- The gap `middleware.ts` does **not** close: every data-bound API client
  (`lib/api-client.ts`/`social-ops-api.ts`/`crm-api.ts`/`sell-machine-api.ts`) calls
  `API_BASE_URL` = the Railway backend **directly** (`antigravity-app-production-175a.up.
  railway.app`), never through the Vercel domain's `/api/v1/*` rewrite — so `middleware.ts` never
  sees these requests at all, and they carry no `Authorization` header today. Separately, the
  backend's own `get_current_user`/`AUTH_ENFORCED` mechanism only verifies its own custom JWT
  (`JWT_SECRET`) — a Supabase-issued token would fail that check even if sent.

## Goals / Non-Goals

**Goals:**
- Every data-bound fetch sends the Supabase access token already sitting in
  `localStorage["token"]`.
- The backend recognizes that same token (verified the same way `middleware.ts` already does) so
  `AUTH_ENFORCED=true` can be flipped without breaking real sessions.

**Non-Goals:**
- **No new login page, no new JWT scheme, no registration endpoint, no client-side route guard.**
  All four existed in the reverted draft and are now recognized as unnecessary — `login.html` +
  `middleware.ts` already do this, more robustly (server-side) than a client hook ever could.
- **No changes to `login.html` or `middleware.ts`** — both are correct and working as-is.
- **Still no role/authorization model inside the FastAPI backend itself** — `middleware.ts`'s
  admin-only gate only protects Vercel-hosted page navigation; the backend's own
  `Depends(get_current_user)` additions in this change only assert "a valid session," not "an
  admin session." Extending backend endpoints to also check `app_metadata.role` is a real,
  separate future decision — not invented here (mirrors the original Non-Goal, just now grounded
  in a real existing role claim instead of an assumed absent one).

## Decisions

1. **The backend's `get_current_user` gains a Supabase-JWT fallback, not a replacement.** When the
   token doesn't verify against the backend's own `JWT_SECRET` (`core/security.py:verify_token`),
   try verifying it as a Supabase-issued JWT (`SUPABASE_JWT_SECRET`, HS256) before giving up. This
   preserves every existing caller of the backend's own JWT (`AuthService.login`,
   demo/db-backed users) unchanged, while newly recognizing the token `login.html` already issues.
2. **`SUPABASE_JWT_SECRET` is declared in `config.py`** (it's already set as a Railway env var,
   confirmed live, just never declared as a `Settings` field — `pydantic-settings`' `extra="ignore"`
   was silently dropping it).
3. **Tenant/identity resolution stays best-effort, matching the existing pattern.** A Supabase
   JWT's `sub` is `auth.users.id` — a different UUID space from `usuarios.id` (used by
   `identity_resolver.resolve_user_uuid`'s email-based lookup). For `growth@contexia.online`/
   `contexia.marketing@gmail.com`, no `usuarios` row exists, so tenant resolution will fall through
   to `None`/the default — **this is fine for CRM/Sell-Machine/Social-Ops**, whose services already
   resolve Cliente Cero server-side by `is_cliente_cero=true` (confirmed in `crm_service.py`), not
   from the caller's JWT tenant claim. `get_current_user`'s job here is "is this session valid,"
   not tenant scoping.
4. **`authenticated-fetch.ts` is now minimal** — just attaches the header from
   `localStorage["token"]` (a key `login.html` already owns and populates) and passes a `401`
   through to the caller (no client-side redirect-and-clear logic — that duplicated
   `middleware.ts`'s server-side job and risked fighting over the same `localStorage`/cookie state
   `login.html` already manages).
5. **`sell_machine_endpoints.py` stays gated per-endpoint, not at router level** (unchanged
   reasoning from the reverted draft — still correct): the Hermes↔backend machine-to-machine bridge
   (`/tasks/*`, `/campaigns/{id}/dispatch`, `/creative-loop/run`, `/telemetry/report`) has no
   browser session; only `/hooks/generate`, `/hooks/evaluate`, `POST /campaigns`, `GET /campaigns`
   get the dependency.

## Risks / Trade-offs

- **[Risk] `bcrypt<4.1` pin (found during the reverted draft) is unrelated to this corrected scope
  but still a real, live bug** → **Kept**: `requirements.txt`'s pin stays, since it protects real
  password verification for any account still using the backend's own `usuarios`/bcrypt path
  (e.g. `AuthService.login`'s DB-backed branch), independent of which auth system this change
  targets.
- **[Trade-off] No admin-role enforcement in the FastAPI backend itself** — accepted per
  Non-Goals; `middleware.ts` already gates the Búnker's page navigation by role, and nothing in
  this repo's current CRM/Sell-Machine/Social-Ops data model requires per-endpoint role checks yet.

## Migration Plan

No schema migration. Stage 11: verify a real Supabase-authenticated session (via the real
`login.html`, using the founder's own credentials — the agent never handles these) sends a token
that the updated `get_current_user` accepts, for each of the five data-bound screens, before
flipping `AUTH_ENFORCED=true`.

## Open Questions

- Should the backend eventually check `app_metadata.role` itself (defense in depth beyond
  `middleware.ts`)? Flagged, not decided here.
