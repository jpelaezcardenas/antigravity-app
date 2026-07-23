# Tasks — Per-Tenant Client Access + Búnker Feeding System

## Stage 1. Schema
- [x] 1.1 Migration: add `email`, `phone`, `contact_name`, `client_tenant_id`, `login_user_id`,
  `provision_status` to `b2b_clients` (idempotent). — `migrations/0027_b2b_clients_contact_and_tenant.sql`

## Stage 2. Per-client tenants + synthetic Shadow GL
- [x] 2.1 Create one `tenants` row per existing client (10) + CÓDIGO 520 (`is_cliente_cero=false`).
- [x] 2.2 Seed distinct synthetic `erp_journal_entries` / `erp_journal_lines` per client tenant
  (opening `1110` balance + recent `4105` sale + `5135` expense), tagged via memo/`source`.
- [x] 2.3 Add CÓDIGO 520 to `b2b_clients`; backfill `email`/`phone`/`contact_name`/`client_tenant_id`
  for all from the source ledger. — `migrations/0028_seed_client_tenants_and_shadow_gl.sql`
- [x] 2.4 Remove Nia Cano entirely (roster row, her tenant, her synthetic Shadow GL, her payment
  history) — founder confirmed she was never an actual Contexia client. She had no login to clean
  up (`provision_status` was `pending_email`, no email in the source ledger). —
  `migrations/0030_remove_nia_cano.sql`. Roster count settles at 10 (9 original + CÓDIGO 520).
- [x] 2.5 Activate CÓDIGO 520 (`status: 'inactivo' → 'activo'`) — founder confirmed it is now
  confirmed to start paying operations. — `migrations/0031_activate_codigo_520.sql`

## Stage 3. Provisioning
- [x] 3.1 Create `auth.users` (+ `auth.identities`) for each client with an email: temp password,
  `email_confirmed_at`, `app_metadata.role='cliente'`. No emails sent. —
  `migrations/0029_provision_client_users.sql`, run by the founder directly in the Supabase SQL
  Editor (creating `auth.users` rows is outside this agent's permitted action set).
- [x] 3.2 Wire `user_tenants` (active membership) + `user_roles` (`viewer`) + `usuarios` to each
  client's own tenant; backfill `b2b_clients.login_user_id` + `provision_status`. Verified: all 10
  clients have an active `user_tenants` membership, a `user_roles` row, a `usuarios` row, and a
  confirmed `auth.users` email.
- [x] 3.3 Reconcile Ferez (canonical Excel email `federicogutierrez.96@gmail.com` used for
  provisioning; the older never-confirmed `fperez@ferez.co` account was left untouched/unused
  rather than deleted). Nia Cano: removed entirely (2.4), not just "no login".
- [x] 3.4 Temporary passwords delivered to the founder and stored in Bitwarden (folder "Contexia -
  Clientes B2B (logins PWA)", 10 items, one per client) — not persisted anywhere else in plaintext.

## Stage 4. Tenant-aware financials (TDD)
- [x] 4.1 Failing test: two tenants → two different snapshots; unresolved authenticated caller → empty.
  — `tests/test_financials_endpoint_tenant_scoping.py`
- [x] 4.2 `financials_endpoints.get_financials`: `Depends(get_current_user)`, resolve caller tenant,
  safe fallback policy (design.md).
- [x] 4.3 Green: targeted backend suite (30/30: 4 new + `test_financials_aggregation` +
  `test_auth_deps`).

## Stage 5. Payments verify
- [x] 5.1 Verified `b2b_payments` already matched the source ledger exactly (Jan–Jun, incl. the
  Repuestos March 1,200,000 typo-correction already in migration 0021) — no reseed needed. CÓDIGO
  520 has no payment rows (not yet paying).

## Stage 6. E2E verification
- [x] 6.1 Identity + data layer proven against real production Supabase: called the real
  `get_financials()` with 3 different provisioned clients' real `resolved_tenant_id` — each returned
  a distinct, correct `caja_real` (Medic $22.6M, Ferez $4.27M, CÓDIGO 520 $290K COP), no cross-client
  leak. Admin-side roster verified via direct query: 10/10 clients `activo` + `provisioned`, payment
  totals match the source ledger. Visual browser login (typing a password) is explicitly outside
  this agent's permitted actions — the founder verifies that step directly once deployed (11.4).

## Stage 7. Feeding system (Phase B)
- [x] 7.1 Backend write endpoints (alta / baja / pago / contact) in `crm_endpoints.py` + `crm_service.py`.
  15 mock-based unit tests (`tests/test_crm_service_b2b_writes.py`).
- [x] 7.2 `B2bRetainersTab.tsx` read → write; `lib/crm-api.ts` write functions. `tsc --noEmit` +
  `next build` both clean.
- [x] 7.3 Provision-on-alta implemented (`create_b2b_client` best-effort calls
  `_provision_b2b_client_login`, never blocks the alta itself on a provisioning failure).
  Accountant admin login: **not done** — her email is still needed (open item, not blocking).

## Stage 11. Deploy to Production (MANDATORY — CLOSES THE LOOP)
See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`
Project-specific: deploy branch `main`; Frontend `https://contexia.online/app/overview`;
Backend `https://antigravity-app-production-175a.up.railway.app`.
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green) + `CACHE_VERSION` bumped
- [ ] 11.3 Railway deploy active (backend financials change)
- [x] 11.4 Production: a client login sees its own Caja Real; admin sees roster — confirmed live
  by the founder for two distinct clients: Medic ($22,600,000) and CÓDIGO 520 ($290,000), both
  exact matches, no cross-client leak.
- [x] 11.5 Report: `openspec/changes/per-tenant-client-access/reports/2026-07-22-deployment.md`
- [x] 11.6 **Critical follow-up (found during 11.4 live testing):** every real client login was
  silently 401'ing — Supabase signs session tokens asymmetrically (ES256 + JWKS), not the legacy
  HS256 shared secret `_verify_supabase_token` only supported. Fixed in `core/deps.py`
  (JWKS-based verification, backward-compatible with legacy HS256), commit `547259d`. Also fixed a
  real, separate CORS gap found en route: `ALLOWED_ORIGINS` on Railway was missing
  `https://www.contexia.online`. See report Stage 11.5 for the full root-cause trail.
