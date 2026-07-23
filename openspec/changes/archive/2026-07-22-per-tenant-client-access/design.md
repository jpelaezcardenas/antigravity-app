# Design — Per-Tenant Client Access

## Identity chain (how a client resolves to its own tenant)
`login.html` (Supabase Auth) → token in `localStorage["token"]` + `sb-access-token` cookie →
`authenticated-fetch.ts` attaches `Authorization: Bearer` → backend `core/deps.py get_current_user`
verifies the Supabase JWT (`SUPABASE_JWT_SECRET`) and calls `core/identity_resolver.py`:
- `resolve_user_uuid(sub, email)`: looks up `usuarios` by email; if none, **falls back to `sub`**
  (= `auth.users.id`).
- `resolve_tenant_uuid(...)`: resolves via the caller's **single active `user_tenants` membership**.

⇒ Wiring `user_tenants(user_id = auth.users.id, tenant_id = <client tenant>, is_active=true)` makes the
caller resolve to its own tenant. We also seed `usuarios(id = auth.users.id, email)` so resolution is
stable if `usuarios` is later populated.

## Financials fallback policy (no cross-client leak)
`GET /api/v1/financials`:
1. `user = Depends(get_current_user)`.
2. If `user.resolved_tenant_id` present → use it.
3. Else if the caller is the **unauthenticated staging user** (no real session) → Cliente Cero (keeps
   local dev + the existing Contexia overview working).
4. Else (authenticated but unresolved tenant) → **empty snapshot** (`caja_real=0, status="empty"`),
   never Cliente Cero.

## Synthetic Shadow GL recipe (distinct per client)
Per client tenant, seed 3 journal entries honoring `financials_service` account classifier
(`1110`=Bancos, `4100/4105`=ventas, `5xxx/6xxx`=gastos):
1. Opening balance (~6 months ago): Dr `1110` X / Cr `3105` X — X distinct per client (derived from a
   per-client base so each Caja Real is visibly different).
2. "Yesterday" sale: Dr `1110` V / Cr `4105` V → `ventas_ayer`.
3. "Yesterday" expense: Dr `5135` G / Cr `1110` G → `gastos_ayer`. Net Caja = X + V − G.

All rows tagged (e.g. `source_ref='synthetic:per-tenant-client-access'`) so they are identifiable and
reversible. `ventas_ayer/gastos_ayer` are date-relative; a static seed shows them the day after seeding.
`caja_real` (cumulative) is always visible — the hero number. Rolling daily reseed = future option.

## Credential handling (safety)
- Users created via SQL with `encrypted_password = crypt(<temp>, gen_salt('bf'))`,
  `email_confirmed_at = now()`, `app_metadata.role='cliente'`. **No emails are sent** (avoids Supabase
  SMTP dependency AND outbound comms to third parties). The founder distributes temp passwords and each
  client resets via the existing `reset-password.html` "Forgot password?" flow.
- No real password is committed to the repo. Temp values are generated at provisioning time and surfaced
  once to the founder.

## Data reconciliation
- **Ferez:** Excel email `federicogutierrez.96@gmail.com` is canonical; the older never-confirmed
  `fperez@ferez.co` is retired.
- **Nia Cano:** no email in the source → gets a tenant + synthetic data + roster contact backfill, but
  **no login** until an email is provided.
- **Repuestos March:** stays 1,200,000 COP (known typo correction, already in `b2b_payments`).
