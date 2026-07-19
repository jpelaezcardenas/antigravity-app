# Deployment Report — crm-b2c-sell-machine-cockpit

**Date:** 2026-07-19

## What shipped

Replaced the Búnker's "B2C / Renta Natural" placeholder tab with a live Kanban funnel:

1. **Data model**: `crm_leads` (4-stage `CHECK`-constrained funnel: `NUEVOS → PROSPECTOS →
   POR_APROBAR → LISTOS_CONTADORA`), `crm_tax_profiles` (1:1 per-lead tax memory for the future
   Taty sales router), `crm_wompi_transactions` (payment record shape mirroring the wizard's
   `payments` table — seeded/simulated only, no live Wompi integration yet), all tenant-scoped to
   Cliente Cero with admin-only RLS (migrations `0022`, `0023`).
2. **Seed**: 4 sample leads (one per stage, obviously fake `SEED-` prefixed names/phones/
   references), each with a tax profile; the `POR_APROBAR` lead has a `PENDING` Wompi transaction,
   the `LISTOS_CONTADORA` lead has an `APPROVED` one — a consistent, idempotent starting state.
3. **Backend**: `GET /api/v1/crm/b2c/pipeline`, `POST /api/v1/crm/leads/{id}/advance`,
   `GET/PATCH /api/v1/crm/leads/{id}/tax-profile`, `POST /api/v1/crm/leads/{id}/approve-payment`
   (the HITL gate: rejects unless the lead is `POR_APROBAR`, then advances it to
   `LISTOS_CONTADORA` and stamps the associated Wompi transaction `APPROVED`) — all under the
   already-live `CRM_CANONICAL` flag, no new flag needed.
4. **Frontend**: `B2cKanbanTab.tsx` (cloning `IdeasTab.tsx`'s click-to-advance idiom, no
   drag-and-drop, no new libraries), wired into `CrmVentasSection.tsx`'s B2C tab, replacing the
   "Próximamente" placeholder entirely.
5. **Docs**: `contexia-app/CLAUDE.md`'s fourth data-bound exception entry updated to describe both
   CRM/Ventas tabs (B2B read-only, B2C reads+writes).

## Commits

- `f32f1c0` — feat(crm): B2C sell-machine schema + seed (Sections 1-3)
- `4c9d3f0` — feat(crm): B2C sell-machine backend service + endpoints (Sections 4-5)
- `b8b93af` — feat(crm): B2C Kanban tab (Section 6) - replaces placeholder
- `a91eeb4` — docs(crm): document B2C Kanban tab as live (Section 7)
- `36a6bb0` — test(crm): verification pass (Sections 8-9) for Change B
- (merge, fast-forward, no conflicts) — `36a6bb0` on `main`
- `ef39ede` — chore(pwa): bump service worker CACHE_VERSION (v10→v11)
- `bd6cdae` — chore(bunker): sync contexia-app build output for B2C Kanban + sw.js bump

## Verification performed

- **Tests**: 26/26 backend tests green (credential-free service-logic + mocked endpoint tests,
  both Change A and B, no regression). `tsc --noEmit` clean, `npm run build` green.
- **DB**: verified live via Supabase MCP — 4 leads across all 4 stages, 4 tax profiles, 2 Wompi
  transactions with correct statuses; RLS + policies present on all 3 new tables; idempotent (seed
  re-applied, counts unchanged).
- **Production — Railway**: `GET /api/v1/crm/b2c/pipeline` → `source: "supabase"`, all 4 seeded
  leads in their correct columns.
- **Production — full UI, full loop**: `/app/bunker` → CRM/Ventas → "B2C / Renta Natural" renders
  the live 4-column board. **Exercised both write actions live in production**:
  - Clicked "Avanzar" on Maria (`NUEVOS`) → confirmed she moved to `PROSPECTOS` on reload.
  - Clicked "Aprobar Pago" on Ana (`POR_APROBAR`) → confirmed she moved to `LISTOS_CONTADORA`, and
    her `crm_wompi_transactions` row was stamped `status: APPROVED`,
    `approved_by: admin@contexia.online` via direct SQL check.
  - **State was then restored** to the documented seed baseline (Maria back to `NUEVOS`, Ana back
    to `POR_APROBAR`, her transaction back to `PENDING`/unstamped) via a one-off SQL correction, so
    future work (and this report) can rely on the documented starting state.
- **Production — no regression**: the B2B tab (Change A) still renders correctly alongside the new
  B2C tab.

## Incidents during this deployment

None new. Applied the lessons from Change A's deployment directly:
- Committed the `sw.js` version bump and pushed it immediately (rather than leaving it uncommitted
  across multiple tool calls), avoiding a repeat of the earlier concurrent-session collision that
  reverted an in-progress edit.
- Used the Python-based, all-characters-safe chunk-reference verifier from the very first sync
  attempt (rather than a fragile shell regex) — **0 missing references on the first try**,
  confirming the missing-chunk incident from Change A will not recur with this process.

## Accepted risk (extends Change A's R1)

`/api/v1/crm/*` endpoints (now including the new B2C routes) carry no per-request auth beyond the
Vercel edge middleware's admin gate on `/app/bunker` and the `CRM_CANONICAL` flag — same posture
Change A already accepted. This change adds a **payment-approval action** behind that same posture,
which is a stronger reason to prioritize the follow-up (request-level auth, e.g. `AUTH_ENFORCED`)
before the Sell Machine's agentic layer (Changes C–G) adds more side-effecting endpoints on top.

## Seeded data caveat

All `crm_wompi_transactions` rows in this change are seeded/simulated (`SEED-REF-...` references) —
there is no live Wompi integration yet (Change C, gated on Wompi keys). Do not mistake this seed
data for real payment activity.

## Known follow-ups (not in this change's scope)

- R1-extended above (request-level auth on CRM endpoints).
- Real Wompi payment link generation + webhook verification — Change C.
- Taty/WhatsApp sales router, reading/writing `crm_tax_profiles` and `crm_leads` — Change D.
- Hermes/Manus agentic layer — Changes E–G.
