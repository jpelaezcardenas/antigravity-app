## Why

Contexia's planned high-volume B2C tax-declaration funnel ("Renta Natural 2026") has no system of
record — no lead tracking, no tax-profile memory, no payment-approval workflow. Change A
(`crm-b2b-retainers-cockpit`, archived) gave the Búnker's "CRM / Ventas" section a live B2B tab; its
"B2C / Renta Natural" tab is still a placeholder. This is Change B: give that tab a real Kanban
funnel backed by real tables, on seeded/simulated data — no external credentials (Wompi, WhatsApp)
required yet, so this ships now and the agentic layer (Taty, Wompi, Hermes/Manus) can build on top
of it later.

## What Changes

- Add three new Supabase tables: `crm_leads` (the funnel roster + stage), `crm_tax_profiles`
  (1:1 per-lead tax memory), `crm_wompi_transactions` (payment record shape, no live Wompi
  integration yet — seeded/simulated only).
- Seed sample leads spread across all 4 funnel stages (`NUEVOS`, `PROSPECTOS`, `POR_APROBAR`,
  `LISTOS_CONTADORA`), idempotently.
- Add endpoints under the existing `CRM_CANONICAL` flag: `GET /api/v1/crm/b2c/pipeline`,
  `POST /api/v1/crm/leads/{id}/advance`, `GET/PATCH /api/v1/crm/leads/{id}/tax-profile`, and
  `POST /api/v1/crm/leads/{id}/approve-payment` (the HITL gate: `POR_APROBAR` → `LISTOS_CONTADORA`).
- Replace the "B2C / Renta Natural" placeholder in `CrmVentasSection.tsx` with a real Kanban tab
  (`B2cKanbanTab.tsx`), cloning the `IdeasTab.tsx` click-to-advance idiom — no drag-and-drop, no new
  libraries.

## Capabilities

### New Capabilities
- `crm-b2c-sell-machine`: B2C lead funnel (Kanban stages), per-lead tax-profile memory, and a
  payment-approval HITL gate, exposed via read/write endpoints and rendered as a Kanban board in
  the Búnker CRM/Ventas section.

### Modified Capabilities
- `crm-b2b-retainers`: no requirement changes — this change only replaces the sibling "B2C /
  Renta Natural" placeholder tab within the same `CrmVentasSection.tsx` shell; the B2B tab and its
  endpoints are untouched.

## Impact

- **Database**: three new tables (`crm_leads`, `crm_tax_profiles`, `crm_wompi_transactions`),
  tenant-scoped to Cliente Cero, admin-only RLS matching Change A's live `role_type` enum pattern.
  No changes to `b2b_clients`/`b2b_payments`.
- **Backend**: new endpoints added to the existing `crm_service.py`/`crm_endpoints.py` (same
  `CRM_CANONICAL` flag — no new flag needed).
- **Frontend**: new `B2cKanbanTab.tsx`; `crm-api.ts` extended (not duplicated) with pipeline/
  advance/tax-profile/approve-payment functions; `CrmVentasSection.tsx`'s B2C tab swapped from
  placeholder to real component.
- **Out of scope (future changes)**: real Wompi payment verification (Change C, gated on Wompi
  keys), Taty/WhatsApp sales router (Change D), Hermes/Manus agentic layer (Changes E–G) — none of
  that is touched here. `crm_wompi_transactions` rows in this change are seeded/simulated only.
