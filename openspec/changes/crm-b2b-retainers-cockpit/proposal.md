## Why

Contexia manages its own B2B retainer clients (Repuestos Don Álvaro, Medic, and 8 others) in a manual
Excel of monthly payments. There is no system view of who is active, what each client pays, or how
retainer revenue trends. The Búnker already reserves a "CRM / Ventas" section, but
`CrmVentasSection.tsx` is a static mock with 5 hardcoded fake clients and no data source. This is
Change A of a staged CRM cockpit + Sell Machine effort — the first, no-external-keys-needed step:
migrate the real B2B retainer ledger into Supabase and give it a live cockpit view.

## What Changes

- Add two new Supabase tables: `b2b_clients` (client roster, status) and `b2b_payments` (a normalized
  ledger, one row per client per month, amounts in COP minor units).
- Seed the 10 real B2B clients with their Jan–Jun 2026 monthly payment history (correcting an
  evident data-entry typo: Repuestos Don Álvaro's March amount is set to 1,200,000 COP to match its
  other 5 months, not the pasted 12,000,000).
- Add `GET /api/v1/crm/b2b/clients` and `GET /api/v1/crm/b2b/payments` endpoints, gated behind a new
  `CRM_CANONICAL` feature flag, following the Supabase-preferred/demo-fallback pattern already used by
  Social Ops.
- Replace the static mock in `CrmVentasSection.tsx` with a tab shell containing a live "B2B / Retainers"
  grid tab (clients × month, with totals), sourced from the new endpoints. A "B2C / Renta Natural"
  tab is added as a placeholder only (its real content is a later change).
- Document this as the third data-bound exception screen in `contexia-app/CLAUDE.md`.

## Capabilities

### New Capabilities
- `crm-b2b-retainers`: Live B2B retainer client roster + monthly payment ledger, exposed via
  read endpoints and rendered as a financial grid in the Búnker CRM/Ventas section.

### Modified Capabilities
(none — `bunker-social-content-ops-port`/`bunker-admin-shell` specs are unaffected; this only adds a
new capability alongside them)

## Impact

- **Database**: two new tables (`b2b_clients`, `b2b_payments`), tenant-scoped to Cliente Cero, RLS
  admin-only. No changes to existing tables.
- **Backend**: new `crm_service.py`, `crm_endpoints.py`, a `CRM_CANONICAL` flag in `config.py`, and a
  new route registration in `router.py`. No changes to existing agents/endpoints.
- **Frontend**: `CrmVentasSection.tsx` is rewritten (tab shell); new `crm-api.ts` client and
  `B2bRetainersTab.tsx` component. The Búnker sidebar/nav is unchanged (the `crm-ventas` slot already
  exists).
- **Docs**: `contexia-app/CLAUDE.md` gains a third data-bound screen entry.
- **Out of scope (future changes)**: B2C Kanban funnel, Wompi payments, Taty/WhatsApp, Hermes/Manus
  agentic layer — none of that is touched here.
