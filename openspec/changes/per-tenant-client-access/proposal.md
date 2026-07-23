# Per-Tenant Client Access + Búnker Feeding System

## Why
Contexia's B2B retainer clients (the `b2b_clients` roster shown in the Búnker) all share a single
tenant (Cliente Cero), and `GET /api/v1/financials` hardcodes that tenant (`_resolve_cliente_cero_tenant_id`).
So today every PWA login lands on `/app/overview` and sees Contexia's own Caja Real — not their own.

The founder needs each client to log in and see THEIR OWN business data (synthetic-but-distinct for
now), a new not-yet-paying client **CÓDIGO 520**, an end-to-end proof, and a durable way for the
founder + accountant to feed the roster (altas / bajas / pagos) from the Búnker.

## What Changes
- **Schema:** add `email`, `phone`, `contact_name`, `client_tenant_id`, `login_user_id`,
  `provision_status` to `b2b_clients`; add CÓDIGO 520 to the roster.
- **Per-client tenants + data:** one `tenants` row per client; distinct synthetic Shadow GL
  (`erp_journal_entries` / `erp_journal_lines`) per tenant so each client's Caja Real differs.
- **Provisioning:** create `auth.users` for each client with an email (temp password, email confirmed,
  **no outbound emails**), seed `app_metadata.role='cliente'`, and wire
  `user_tenants` / `user_roles` / `usuarios` to each client's own tenant.
- **Tenant-aware financials:** `GET /api/v1/financials` resolves the caller's tenant from the session;
  falls back to Cliente Cero only for the unauthenticated/local path, and returns an empty snapshot
  (never Cliente Cero) for an authenticated caller with no tenant — no cross-client leak.
- **Feeding system (Phase B):** turn the read-only Búnker B2B tab into read-write (alta / baja / pago /
  contact capture) with new backend write endpoints; provision-on-alta; accountant admin login.

## Impact
- **Specs:** NEW `per-tenant-client-access`; builds on archived `crm-b2b-retainers` (roster/payments
  already seeded and correct — Repuestos March = 1,200,000 COP, the known-typo correction stands).
- **Code:** `apps/backend/presentation/financials_endpoints.py`; new migrations + provisioning script;
  `contexia-app` CRM B2B tab + `lib/crm-api.ts` (Phase B).
- **Data:** writes to production Supabase (`kpynymwghfwshvcvevxq`) — tenants, auth users, journals.
- **Non-goals:** per-client REAL data ingestion (DIAN/Siigo per client); making Pulso/Radar/Patrimonio
  and other end-user screens tenant-aware (only `financials` / CashTodayCard in this change);
  enabling Supabase SMTP / sending invite emails to clients.
