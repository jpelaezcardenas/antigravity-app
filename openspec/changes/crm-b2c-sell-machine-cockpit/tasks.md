## 1. Setup + schema verification

- [x] 1.1 Created branch `feature/crm-b2c-sell-machine-cockpit`; committing each section promptly
      given the demonstrated shared-working-directory collision risk from Change A.
- [x] 1.2 Re-verified live: Cliente Cero tenant id unchanged (`e2d30d09-6b96-4ebe-a79a-c6aff7a5df34`),
      and `crm_leads`/`crm_tax_profiles`/`crm_wompi_transactions` names confirmed free.

## 2. Migration (DDL) — TDD

- [x] 2.1 Wrote `apps/backend/tests/test_crm_b2c_schema.py` (RUN_CRM_B2B=1-gated). Confirmed failing
      (tables didn't exist).
- [x] 2.2 Authored `apps/backend/migrations/0022_crm_b2c_sell_machine.sql`: `crm_leads` (`stage` via
      `CHECK` constraint, `UNIQUE(tenant_id, whatsapp_phone)`), `crm_tax_profiles`
      (`UNIQUE(lead_id)`), `crm_wompi_transactions` (`reference UNIQUE`, FK `lead_id`) — RLS
      admin-only using the live `role_type` enum (`role = 'admin'`), `updated_at` triggers (reusing
      `update_crm_b2b_updated_at()` from Change A), idempotent DDL.
- [x] 2.3 Applied via Supabase MCP `apply_migration`. Verified live: all 3 tables exist with
      `relrowsecurity = true` and their `*_admin_only` policies present.

## 3. Seed (idempotent) — TDD

- [x] 3.1 (covered by `test_crm_b2c_schema.py`) — asserts leads across all 4 stages, every lead has
      a tax profile, and `POR_APROBAR` leads have a pending Wompi transaction.
- [x] 3.2 Authored `apps/backend/migrations/0023_seed_crm_b2c_leads.sql`: 4 sample leads (one per
      stage, `SEED-` prefixed names/phones), 4 tax profiles, and 2 Wompi transactions
      (`SEED-REF-...` references — one `PENDING` for the `POR_APROBAR` lead, one `APPROVED` for the
      `LISTOS_CONTADORA` lead), idempotent via `ON CONFLICT`.
- [x] 3.3 Applied via Supabase MCP; verified live (4 leads across all 4 stages, 4 tax profiles, 2
      transactions); re-applied the full seed a second time — counts unchanged, confirming
      idempotency.

## 4. Backend service — TDD

- [ ] 4.1 Write failing unit tests (credential-free, mocked Supabase client per
      `test_crm_service_grid_logic.py`'s pattern) for new `crm_service.py` methods:
      `b2c_pipeline()`, `advance_lead(lead_id, stage)` (including the invalid-stage-4xx case),
      `get_tax_profile(lead_id)`/`update_tax_profile(lead_id, patch)`, and
      `approve_payment(lead_id, approved_by)` (including the not-`POR_APROBAR`-rejected case).
      Wrote `test_crm_service_b2c_logic.py` (credential-free, mocked client, mirrors
      `test_crm_service_grid_logic.py`). Confirmed failing (methods didn't exist).
- [x] 4.2 Extended `apps/backend/services/crm_service.py` with `b2c_pipeline`, `advance_lead`,
      `get_tax_profile`, `update_tax_profile`, `approve_payment` (Supabase-preferred/demo-fallback
      idiom where applicable; writes go through `get_service_supabase()` per Change A's Decision 8).
- [x] 4.3 8/8 new tests green; re-ran Change A's `test_crm_service_grid_logic.py` alongside —
      14/14 total, no regression.

## 5. Backend endpoints — TDD

- [x] 5.1 Wrote `test_crm_b2c_endpoints.py` (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`, per Change A's pattern). Confirmed failing (routes
      didn't exist — 404s).
- [x] 5.2 Added the 4 routes to `apps/backend/presentation/crm_endpoints.py` (same router, same
      `CRM_CANONICAL` flag already registered in `router.py` — no new flag needed).
- [x] 5.3 12/12 endpoint tests green (7 new + 5 from Change A), no regression.

## 6. Frontend client + Kanban tab

- [x] 6.1 Extended `contexia-app/lib/crm-api.ts` with `getB2cPipeline()`,
      `advanceCrmLead(id, stage)`, `getCrmTaxProfile(id)`, `updateCrmTaxProfile(id, patch)`,
      `approveCrmPayment(id, approvedBy)` and their TypeScript types (`CrmPipelineResponse`,
      `CrmLead`, `CrmStage`, `CrmTaxProfile`).
- [x] 6.2 Created `contexia-app/components/bunker/crm/B2cKanbanTab.tsx`: `COLUMNS` for the 4
      stages, `load()` in `useEffect(...,[])` with `loading`/`error`/`source` states, `useMemo`
      grouping by stage, an `advance(lead)` handler (await `advanceCrmLead` then reload), an
      "Aprobar Pago" button rendered only on `POR_APROBAR` cards (calls `approveCrmPayment` then
      reload). CSS-grid columns, `@theme` tokens only — no drag-and-drop, no new libraries.
- [x] 6.3 Wired `B2cKanbanTab` into `CrmVentasSection.tsx`'s "B2C / Renta Natural" tab, replacing
      the "Próximamente" placeholder text entirely.

Verification: `tsc --noEmit` clean, `npm run build` green.

## 7. Docs

- [x] 7.1 Updated the CRM/Ventas entry in `contexia-app/CLAUDE.md`'s *Pantallas data-bound* section
      (and the top-level "Reglas duras" bullet) to describe both live tabs: B2B read-only, B2C
      reads + writes (advance, approve-payment HITL) — no longer a placeholder.
- [x] 7.2 Confirmed the `crm-b2c-sell-machine` delta spec is in place at
      `specs/crm-b2c-sell-machine/spec.md`, ready for archive-time sync.

## 8. Verify + DB state (MANDATORY before Stage 11)

- [x] 8.1 Ran the full targeted backend + frontend test suites: 26/26 backend tests green
      (credential-free, both Change A and B, no regression); `tsc --noEmit` clean; `npm run build`
      green.
- [x] 8.2 Verified live DB state via Supabase MCP: 1 lead per stage (all 4 present), 4 tax
      profiles, 2 Wompi transactions (1 PENDING, 1 APPROVED) with SEED-prefixed values; RLS +
      policies present on all 3 tables; idempotency re-confirmed (seed re-applied, counts
      unchanged).
- [x] 8.3 Wrote `openspec/changes/crm-b2c-sell-machine-cockpit/reports/2026-07-19-step8-verification.md`.

## 9. E2E (browser)

- [x] 9.1 Opened the Búnker (local dev server), navigated CRM/Ventas → "B2C / Renta Natural":
      confirmed the placeholder text is completely gone and the real 4-column Kanban board renders
      in its place. With the (not-yet-deployed) backend unreachable locally, confirmed the tab
      shows an explicit error state (not blank) while still rendering the board shell — matches
      the established pattern. The full live-data walkthrough (real seeded leads populating each
      column, advance/approve-payment actually moving cards) requires the new endpoints to be
      deployed — deferred to the Stage 11 prod smoke-test, same as Change A.

## 10. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 10.1 Committed migrations/backend/frontend in scoped commits across `feature/crm-b2c-sell-machine-cockpit`.
- [x] 10.2 Merged to `main` (fast-forward, no conflicts) and pushed.
- [x] 10.3 Confirmed Railway backend deploy `SUCCESS`. `CRM_CANONICAL` was already `true` from
      Change A — the new B2C endpoints went live immediately on this deploy.
- [x] 10.4 Bumped `contexia-app/public/sw.js` `CACHE_VERSION` (v10→v11, committed and pushed
      immediately this time to avoid the earlier concurrent-session collision pattern), rebuilt,
      and synced `contexia-app/out/` → `app/` additively using the **Python-based chunk-reference
      verifier from the start** (handles all filename characters including `~`) — **0 missing
      references on the first attempt**, confirming the lesson from Change A's incident held.
      Confirmed Vercel deploy `READY`.
- [x] 10.5 Verified live at `https://contexia.online/app/bunker` → CRM/Ventas: B2B tab still works
      (no regression); "B2C / Renta Natural" tab renders the real Kanban board with all 4 seeded
      leads in their correct columns, `Fuente: supabase`.
- [x] 10.6 Exercised the full loop live in production: clicked "Avanzar" on Maria (`NUEVOS` →
      `PROSPECTOS`) — confirmed via UI reload. Clicked "Aprobar Pago" on Ana (`POR_APROBAR`) —
      confirmed she moved to `LISTOS_CONTADORA` and her `crm_wompi_transactions` row was stamped
      `APPROVED`/`approved_by: admin@contexia.online` via direct SQL check. **State was then
      restored** to the documented seed baseline via a follow-up SQL update (not a new migration —
      a one-off restoration, since the mutation was itself proof the feature works) so future work
      finds the documented starting point.
- [x] 10.7 Created deployment report at
      `openspec/changes/crm-b2c-sell-machine-cockpit/reports/2026-07-19-deployment.md`.

## 11. Archive

- [x] 11.1 Synced the `crm-b2c-sell-machine` capability into `openspec/specs/` and archived this
      change to `openspec/changes/archive/2026-07-19-crm-b2c-sell-machine-cockpit/`.
