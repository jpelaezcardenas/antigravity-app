# Tasks: freemium-tenant-minimum-seed

## 1. `shadow_gl_seed_service.py` — new seed function (TDD)

- [ ] 1.1 Write failing tests: seeds exactly one `-OPEN` entry + 2 lines (1110 debit / 3105
      credit) for the given tenant/nit/amount; idempotent on a second call (no duplicate); never
      touches another tenant's rows.
- [ ] 1.2 Implement `seed_freemium_opening_balance(client, tenant_id, nit, name,
      opening_balance_cents)` in new `apps/backend/services/shadow_gl_seed_service.py`, mirroring
      migration `0028`'s SQL pattern via the Supabase client (existence check on
      `external_reference_id = f"SYNTH-{nit}-OPEN"` scoped to `tenant_id`, then insert entry +
      lines).
- [ ] 1.3 Tests green.

## 2. Wire into `create_b2b_client`

- [ ] 2.1 Write failing tests: `plan_tier="freemium"` + `opening_balance_cents > 0` calls the seed
      function with the new tenant's id; `opening_balance_cents` omitted or 0 → no seed call;
      any non-freemium tier + `opening_balance_cents` provided → no seed call, alta still
      succeeds.
- [ ] 2.2 Add `opening_balance_cents: Optional[int] = None` parameter to `create_b2b_client`
      (`apps/backend/services/crm_service.py`); after the `tenants` insert succeeds, call
      `seed_freemium_opening_balance` when gated conditions hold.
- [ ] 2.3 Tests green.

## 3. Endpoint

- [ ] 3.1 Add `opening_balance_cents: Optional[int] = None` to `CreateB2bClientRequest`
      (`apps/backend/presentation/crm_endpoints.py`), passed through to `create_b2b_client`.

## 4. Frontend

- [ ] 4.1 Add optional "Saldo de apertura (COP)" numeric input to the alta form in
      `B2bRetainersTab.tsx`, rendered only when the selected tier is `freemium`; add
      `opening_balance_cents?: number` to `CreateB2bClientInput` in `lib/crm-api.ts`.

## 5. Testing

- [ ] 5.1 Run full backend suite (`-k "crm or shadow_gl"` plus a broader sweep) — confirm no
      regressions.
- [ ] 5.2 `tsc --noEmit` on `contexia-app/` — zero errors.

## 6. Reports

- [ ] 6.1 Write `progress/impl_freemium-tenant-minimum-seed.md`.

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green)
- [ ] 11.3 Railway deploy active (backend change)
- [ ] 11.4 Production URL: changes visible and working
- [ ] 11.5 Create report: openspec/changes/freemium-tenant-minimum-seed/reports/YYYY-MM-DD-deployment.md
