# Authentication & Routing Architecture

> Last updated: 2026-07-28 (`surface-and-routing-standardization`)
> See also: ARCHITECTURE.md Decision #18

## Canonical Login

`/login.html` is the **ONLY valid login** for Contexia. It is a standalone static HTML file
(not a Next.js page) that authenticates against **Supabase Auth** via the browser SDK.

After successful authentication it stores:
- `localStorage["token"]` — the Supabase access token (used by `lib/authenticated-fetch.ts` for backend API calls)
- Cookie `sb-access-token` — the same token, read by Vercel Edge Middleware for server-side route gating

Role-based destination after login (`destinationForRole()` in `login.html`):
- Admin (`app_metadata.role` ∈ `{admin, superadmin, contexia_admin}`) → `/app/bunker`
- Client (any other authenticated user) → `/app/overview`

**Hard rule**: no agent may create alternative login pages, inline auth checks, or Supabase
`signInWithPassword` flows anywhere other than `login.html`. The legacy inline login at
`app-admin/index.html` was permanently deleted (2026-07-28).

## Middleware (`middleware.ts`)

Vercel Edge Middleware gates all non-public routes. It verifies the `sb-access-token` cookie
using HS256 HMAC with `SUPABASE_JWT_SECRET`.

### Public paths (no auth required)

`/`, `/landing.html`, `/login.html`, `/reset-password.html`, `/logout.html`,
`/crear-empresa*`, `/wizard/*`, `/_next/*`, `/assets/*`, `/app/dashboard-assets/*`,
`/app/assets/*`, `/404.html`, `/_not-found.html`

### Protected paths

All other paths require a valid, non-expired JWT in `sb-access-token`.
Missing or invalid token → 302 to `/login.html?next=<original-path>`.

### Admin-only paths

`/app-admin/*` requires `role ∈ {admin, superadmin, contexia_admin}` (extracted from
`app_metadata.role`, `app_metadata.account_role`, `user_metadata.role`, or `user_metadata.roles`
array). Non-admin → 302 to `/app/overview`.

### Special routing rules

| Path | Behavior |
|---|---|
| `/app` (exact) | 302 → `/app/bunker` (all authenticated users) |
| `/app/<unknown>` | 302 → `/app/bunker` (admin) or `/app/overview` (client) |
| Known app paths | Pass through (served by vercel.json rewrites) |

Known app paths: `/app/overview`, `/app/fiscal`, `/app/radar`, `/app/patrimonio`,
`/app/config`, `/app/flujo-detalle`, `/app/bunker`

## Surface Map

| Route | Source | Shell | Role | Per-tenant | Notes |
|---|---|---|---|---|---|
| `/login.html` | `login.html` (standalone) | None | None | No | ONLY valid login |
| `/app/overview` | `contexia-app/(shell)/overview` | TopBar + BottomNav | Any auth | Yes (Caja Real, Alerts) | Mobile-first PWA |
| `/app/fiscal` | `contexia-app/(shell)/fiscal` | TopBar + BottomNav | Any auth | Designed for | Mobile-first PWA |
| `/app/radar` | `contexia-app/(shell)/radar` | TopBar + BottomNav | Any auth | Designed for | Mobile-first PWA |
| `/app/patrimonio` | `contexia-app/(shell)/patrimonio` | TopBar + BottomNav | Any auth | Designed for | Mobile-first PWA |
| `/app/config` | `contexia-app/(shell)/config` | TopBar + BottomNav | Any auth | No (user settings) | Rebuilt as React component |
| `/app/flujo-detalle` | `contexia-app/flujo-detalle` | Detail (back btn) | Any auth | Yes (Liquidity Bridge) | No BottomNav |
| `/app/bunker` | `contexia-app/app/bunker` | BunkerSidebar | All auth (role-filtered) | Mixed | Desktop-first, premium design |

## Bunker Role-Based Sections

The Bunker (`/app/bunker`) is a shared surface — same route, different section visibility.

| Section | Admin | Client |
|---|---|---|
| Dashboard | Yes | Yes |
| CRM / Ventas | Yes | No |
| Social Content Ops | Yes | No |
| Onboarding | Yes | No |
| Sell Machine | Yes | No |
| Agentic OS | Yes | Yes |
| Configuración | Yes | Yes |

Implementation: `BunkerSidebar.tsx` reads `isAdmin` prop. The Bunker page (`page.tsx`) reads
the user role from the JWT cookie (`sb-access-token`) client-side via `readRoleFromJwt()`.
Admin roles: `admin`, `superadmin`, `contexia_admin`. Admin-only sections are defined in
`ADMIN_ONLY_SECTIONS` array. Non-admin users attempting to access an admin section via deep
link see the Dashboard instead (fail-safe guard in `handleSelectSection`).

## vercel.json Routing

### Redirects (URL changes in browser)

- `/` → `/landing.html`
- `/login` → `/login.html`
- `/app` → `/app/bunker` (302, not permanent)
- `/logout` → `/logout.html`

### Rewrites (transparent, URL stays the same)

- `/api/v1/*` → Railway backend (`antigravity-app-production-175a.up.railway.app`)
- `/app/overview` → `/app/overview.html` (and similarly for fiscal, radar, patrimonio, config, bunker)
- `/app/dashboard-assets/*` → `/app-admin/dashboard-assets/*`
- `/app/*` (catch-all) → `/404.html` (defense-in-depth; middleware redirects before this is reached)

### Cache headers

All `/app/*` and `/app-admin/*` paths: `private, no-store, max-age=0, must-revalidate`
(prevents stale HTML from browser/CDN cache after deploys).

## Deleted Surfaces (2026-07-28)

| File | Why deleted |
|---|---|
| `app/index.html` | Orphaned — no rewrite pointed to it, loaded Vite SPA without auth |
| `app-admin/index.html` | Legacy admin shell with rogue inline login that bypassed `login.html` |
| `app-admin/dashboard-assets/index-DblwMcm3.js` | No-auth variant of Vite SPA bundle |

## Backend Auth (for reference)

Backend auth is independent of frontend routing:
- `AUTH_ENFORCED=true` in production (Railway)
- JWT verification: `core/deps.py::_verify_supabase_token` (supports both HS256 and ES256/JWKS)
- Tenant resolution: `core/tenant_context.py::resolve_request_tenant_scope()` (Decision #17)
- All agent endpoints require `Depends(get_current_user)` (Decision #17)
