# Proposal: freemium-tenant-minimum-seed

## Why

A freemium lead provisioned via `crm-alta-tiered-provisioning` has zero Siigo/DIAN data on day
one. Freemium only unlocks `pulso_diario` (`plan-tier-feature-gating`), and `CashTodayCard` is the
one screen that feature actually renders — with no Shadow GL rows, it shows an `empty` state
instead of the "here's your real cash position" promise that closes the sale. This change gives
the alta flow an optional way to seed a minimal, honest opening balance so a new freemium tenant's
first screen isn't blank.

## What Changes

- New optional `opening_balance_cents` field on `POST /api/v1/crm/b2b/clients`, applied only when
  `plan_tier == "freemium"`. When provided and > 0, writes a single synthetic opening-balance
  journal entry (account `1110` Bancos / `3105` Capital) into the new tenant's own Shadow GL,
  reusing the exact `SYNTH-{nit}-OPEN` / `SYNTH:per-tenant-client-access` convention from migration
  `0028` — never touching Cliente Cero, never any other tenant.
- Deliberately does **not** seed synthetic `ventas_ayer`/`gastos_ayer` (no fabricated "yesterday's
  sales" for a lead who hasn't operated yet) — an opening balance is an honest "here is your
  starting capital," not invented activity. `caja_real` becomes non-zero; `ventas_ayer`/
  `gastos_ayer` correctly show 0 until real data or Subdomain 6's agent path lands.
- No new migration, no new reseed cron job: an `-OPEN` entry is never re-dated by the existing
  rolling-reseed job (`0035`), so this requires zero new infrastructure.
- `B2bRetainersTab.tsx` alta form gains an optional "Saldo de apertura (COP)" input, shown only
  when the selected tier is `freemium`.

## Capabilities

### New Capabilities
None — this extends the existing `crm-b2b-retainers` alta capability (delta below).

### Modified Capabilities
- `crm-b2b-retainers` — alta accepts an additional optional field; no existing requirement's
  contract changes (backwards compatible: field is optional, defaults to no seed).

## Impact

- `apps/backend/services/crm_service.py` (`create_b2b_client`) — reads `opening_balance_cents`
  from the request, calls a new seed function when tier is `freemium` and value > 0.
- New `apps/backend/services/shadow_gl_seed_service.py` — `seed_freemium_opening_balance()`,
  mirrors migration `0028`'s SQL pattern via the Supabase client, idempotent
  (`external_reference_id = SYNTH-{nit}-OPEN` existence check).
- `apps/backend/presentation/crm_endpoints.py` — `CreateB2bClientRequest` gains
  `opening_balance_cents: Optional[int] = None`.
- `contexia-app/lib/crm-api.ts` / `B2bRetainersTab.tsx` — optional input field, freemium-only.
- No migrations. No changes to `financials_service.py` (account codes `1110`/`3105` already
  correctly classified).
