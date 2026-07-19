## 1. Setup + schema verification

- [ ] 1.1 Create branch `feature/crm-b2c-sell-machine-cockpit`; capture `git status` baseline.
      Re-confirm this repo's shared-working-directory risk from Change A: commit each completed
      section promptly rather than batching, in case a concurrent session touches the same tree.
- [ ] 1.2 Re-verify live: `tenants.is_cliente_cero` tenant id unchanged, `user_roles.role` enum
      labels unchanged, and confirm `crm_leads`/`crm_tax_profiles`/`crm_wompi_transactions` names
      are free (no collision with existing tables).

## 2. Migration (DDL) — TDD

- [ ] 2.1 Write a failing schema-assertion test (`test_crm_b2c_schema.py`, gated `RUN_CRM_B2B=1`
      to reuse Change A's existing gate, or a new `RUN_CRM_B2C=1`) asserting the three tables exist
      with RLS enabled.
- [ ] 2.2 Author `apps/backend/migrations/0022_crm_b2c_sell_machine.sql`: `crm_leads` (`stage` via
      `CHECK` constraint, `UNIQUE(tenant_id, whatsapp_phone)`), `crm_tax_profiles`
      (`UNIQUE(lead_id)`), `crm_wompi_transactions` (`reference UNIQUE`, FK `lead_id`) — RLS
      admin-only using the live `role_type` enum (`role = 'admin'`), `updated_at` triggers,
      idempotent DDL (`IF NOT EXISTS`; `DROP POLICY IF EXISTS ... ; CREATE POLICY ...`).
- [ ] 2.3 Apply via Supabase MCP `apply_migration`; confirm all three tables exist and RLS is
      enabled with policies present (verify live via SQL, don't just trust the migration file).

## 3. Seed (idempotent) — TDD

- [ ] 3.1 Write a failing test asserting: sample leads exist spread across all 4 stages, each has
      a `crm_tax_profiles` row, and `POR_APROBAR` leads have an associated pending
      `crm_wompi_transactions` row (needed to exercise the approve-payment flow end-to-end).
- [ ] 3.2 Author `apps/backend/migrations/0023_seed_crm_b2c_leads.sql`: insert sample leads (obvious
      placeholder names/phones, e.g. prefixed `SEED-`), one `crm_tax_profiles` row each, and
      `crm_wompi_transactions` rows for `POR_APROBAR` leads with clearly-fake `reference` values
      (e.g. `SEED-REF-...`) so they can never be confused with real payment activity — using
      `ON CONFLICT (tenant_id, whatsapp_phone) DO UPDATE` for idempotency.
- [ ] 3.3 Apply via Supabase MCP; re-apply once more to prove idempotency (row counts unchanged).

## 4. Backend service — TDD

- [ ] 4.1 Write failing unit tests (credential-free, mocked Supabase client per
      `test_crm_service_grid_logic.py`'s pattern) for new `crm_service.py` methods:
      `b2c_pipeline()`, `advance_lead(lead_id, stage)` (including the invalid-stage-4xx case),
      `get_tax_profile(lead_id)`/`update_tax_profile(lead_id, patch)`, and
      `approve_payment(lead_id, approved_by)` (including the not-`POR_APROBAR`-rejected case).
- [ ] 4.2 Extend `apps/backend/services/crm_service.py` with these methods (same
      Supabase-preferred/demo-fallback idiom, `get_service_supabase()` reads/writes as established
      in Change A).
- [ ] 4.3 Run tests green.

## 5. Backend endpoints — TDD

- [ ] 5.1 Write failing endpoint tests (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`, per Change A's `test_crm_endpoints.py` pattern —
      the sync `TestClient` remains broken in this environment) for all 4 new routes, including the
      4xx cases (invalid stage, approve-payment on a non-`POR_APROBAR` lead).
- [ ] 5.2 Add the 4 routes to `apps/backend/presentation/crm_endpoints.py` (same router, same
      `CRM_CANONICAL` flag already registered in `router.py` — no new flag needed).
- [ ] 5.3 Run tests green.

## 6. Frontend client + Kanban tab

- [ ] 6.1 Extend `contexia-app/lib/crm-api.ts` with `getB2cPipeline()`, `advanceCrmLead(id, stage)`,
      `getCrmTaxProfile(id)`, `updateCrmTaxProfile(id, patch)`, `approveCrmPayment(id, approvedBy)`
      and their TypeScript types (board-shaped `CrmPipelineResponse`, `CrmLead`, `CrmStage`).
- [ ] 6.2 Create `contexia-app/components/bunker/crm/B2cKanbanTab.tsx`: `COLUMNS` for the 4 stages,
      `load()` in `useEffect(...,[])` with `loading`/`error`/`source` states, `useMemo` grouping by
      stage, a `move(leadId, stage)` handler (await `advanceCrmLead` then reload), an
      "Aprobar Pago" button rendered only on `POR_APROBAR` cards (calls `approveCrmPayment` then
      reload). CSS-grid columns, `@theme` tokens only — no drag-and-drop, no new libraries.
- [ ] 6.3 Wire `B2cKanbanTab` into `CrmVentasSection.tsx`'s "B2C / Renta Natural" tab, replacing the
      "Próximamente" placeholder text entirely.

## 7. Docs

- [ ] 7.1 Update the CRM/Ventas entry in `contexia-app/CLAUDE.md`'s *Pantallas data-bound* section
      to note the B2C tab is now live (reads + writes: advance, tax-profile update, approve
      payment) rather than a placeholder — this doesn't add a new numbered exception (the section
      itself is unchanged, its content is what's now live).
- [ ] 7.2 Confirm the `crm-b2c-sell-machine` delta spec is in place at
      `specs/crm-b2c-sell-machine/spec.md`, ready for archive-time sync.

## 8. Verify + DB state (MANDATORY before Stage 11)

- [ ] 8.1 Run the full targeted backend + frontend test suites; confirm green (`tsc --noEmit`,
      `npm run build`).
- [ ] 8.2 Verify live DB state via Supabase MCP: seeded leads/tax-profiles/transactions counts and
      shapes match the fixture; re-confirm idempotency; confirm RLS enabled and policies present on
      all three new tables.
- [ ] 8.3 Write `openspec/changes/crm-b2c-sell-machine-cockpit/reports/YYYY-MM-DD-step8-verification.md`.

## 9. E2E (browser)

- [ ] 9.1 Open the Búnker, navigate CRM/Ventas → "B2C / Renta Natural", confirm: 4 columns render
      with seeded leads in the correct columns, no "Próximamente" text remains, advancing a lead
      via the UI moves it between columns, and approving payment on a `POR_APROBAR` lead moves it
      to `LISTOS_CONTADORA` and is reflected on reload.

## 10. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 10.1 Commit the migrations, backend, and frontend changes in scoped commits, referencing this
      change id.
- [ ] 10.2 Merge to `main` (resolve any conflicts against concurrent work carefully — do not
      overwrite unrelated in-progress changes) and push.
- [ ] 10.3 Confirm Railway backend deploy completes green. `CRM_CANONICAL` is already `true` in
      production from Change A — the new B2C endpoints go live immediately on this deploy; there is
      no dark-deploy step for the flag itself here (only the new routes are new).
- [ ] 10.4 **Bump `contexia-app/public/sw.js` `CACHE_VERSION`**, rebuild (`npm run build`), and
      sync `contexia-app/out/` → `app/` additively. **Use a chunk-reference verifier that handles
      all filename characters including `~`** (Change A's initial grep-based check missed `~` and
      caused a production 404 — use the Python-based parser approach from that incident, not a
      shell regex). Confirm Vercel deploy green.
- [ ] 10.5 Verify live at `https://contexia.online/app/bunker` → CRM/Ventas → "B2C / Renta Natural":
      real Kanban board renders with seeded leads across all 4 columns.
- [ ] 10.6 In production, exercise the full loop once: advance a lead from `NUEVOS` to
      `PROSPECTOS` via the UI, and approve payment on a `POR_APROBAR` lead, confirming it reaches
      `LISTOS_CONTADORA` — then, if these were real seed rows (not a copy meant to stay pristine),
      note in the deployment report whether state was left mutated or restored.
- [ ] 10.7 Create deployment report at
      `openspec/changes/crm-b2c-sell-machine-cockpit/reports/YYYY-MM-DD-deployment.md`, including
      an explicit reminder of the R1-style accepted-auth-risk note (now covering a payment-approval
      action, not just reads) and the seeded-`crm_wompi_transactions`-is-not-real caveat.

## 11. Archive

- [ ] 11.1 Sync the `crm-b2c-sell-machine` capability into `openspec/specs/` and archive this change
      once Stage 11 is confirmed complete and verified live.
