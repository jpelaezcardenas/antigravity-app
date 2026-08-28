# Review — task freemium-tenant-minimum-seed

**Verdict:** APPROVED

## Checkpoints
- C1 (architecture/tenant boundaries): [x] `shadow_gl_seed_service.py` scopes every insert/select
  to `tenant_id` explicitly (lines 33-77), never hardcodes Cliente Cero, and `crm_service.py:264`
  passes `client_tenant_id` from the just-created tenant row — no cross-tenant write possible.
- C2 (account codes / naming convention match migration 0028): [x] Verified 1110 debit / 3105
  credit, `SYNTH-{nit}-OPEN`, memo prefix `SYNTH:per-tenant-client-access` — byte-for-byte match
  against `apps/backend/migrations/0028_seed_client_tenants_and_shadow_gl.sql:52-67`.
- C3 (idempotency): [x] `shadow_gl_seed_service.py:33-41` checks `external_reference_id` scoped to
  `tenant_id` before insert, mirrors 0028's own guard (0028 line 115).
- C4 (0035 reseed cron never touches -OPEN): [x] `0035_rolling_reseed_synthetic_shadow_gl.sql:30-32`
  and `:49-51` WHERE clauses require `external_reference_id LIKE '%-SALE' OR '%-EXPENSE'` — `-OPEN`
  is structurally excluded. Implementer's claim confirmed by direct read, not taken on faith.
- C5 (gating logic in `create_b2b_client`): [x] `crm_service.py:264` — `plan_tier == "freemium" and
  opening_balance_cents` (truthy, covers `None` and `0`); any other tier or falsy value is a silent
  no-op, no exception. Confirmed by the 3 targeted tests in `test_crm_service_b2b_writes.py:118-197`
  (freemium+amount seeds, freemium+no-amount doesn't, non-freemium ignores — real gating coverage,
  not just happy path).
- C6 (endpoint validation): [x] `crm_endpoints.py:49` — `opening_balance_cents: Optional[int] =
  Field(default=None, ge=0)`, passed through only when non-None (`:68-69`).
- C7 (frontend): [x] `B2bRetainersTab.tsx:318` renders the input only when `altaPlanTier ===
  "freemium"`; submission (`:124-127`) sends the field only for freemium with a non-empty value,
  converts COP → minor units via `Math.round(Number(...) * 100)`. `crm-api.ts:92` adds the optional
  field to `CreateB2bClientInput` correctly.
- C8 (tests green): [x] `python -m pytest tests/test_shadow_gl_seed_service.py
  tests/test_crm_service_b2b_writes.py tests/test_crm_endpoints.py tests/test_plan_features.py -q`
  → `41 passed`, run independently by the reviewer, not trusted from the implementer's report.
- C9 (delta is genuine, not already-present): [x] `openspec/specs/crm-b2b-retainers/spec.md` (main
  synced spec) contains only the base `plan_tier` requirement text (lines 80-86) — no
  `opening_balance_cents`/freemium-seed language anywhere in that file. Confirmed via grep. The
  delta in `openspec/changes/freemium-tenant-minimum-seed/specs/crm-b2b-retainers/spec.md` is a
  real MODIFIED addition, not a duplicate.
- C10 (docs-sync): [x] No architecture container/dependency changed (reuses existing Shadow GL
  tables and the existing `create_b2b_client` call), so no `ARCHITECTURE.md` update was required.
  Correctly not touched.
- C11 (clean diff / no unrelated files): [ ] ← `git status --short` shows `AGENTES.md` and
  `progress/current.md` modified, plus untracked `ai-specs/references/`, none of which are part of
  this change's scope (AGENTES.md diff is the pre-existing 2026-08-16 WhatsApp inbound-only rule;
  progress/current.md diff reconciles state from a 2026-08-17 session predating this change). These
  are leftovers from other parallel sessions and must NOT be staged/committed as part of this
  change's commit.

## Required changes (if any)
1. Before committing/staging this change, explicitly exclude `AGENTES.md`, `progress/current.md`,
   and `ai-specs/references/` from `git add` — stage only the files listed in the implementer's
   report (`apps/backend/services/shadow_gl_seed_service.py`,
   `apps/backend/tests/test_shadow_gl_seed_service.py`, `apps/backend/services/crm_service.py`,
   `apps/backend/presentation/crm_endpoints.py`, `apps/backend/tests/test_crm_service_b2b_writes.py`,
   `contexia-app/lib/crm-api.ts`, `contexia-app/components/bunker/crm/B2bRetainersTab.tsx`,
   `openspec/changes/freemium-tenant-minimum-seed/`, `progress/impl_freemium-tenant-minimum-seed.md`,
   `progress/review_freemium-tenant-minimum-seed.md`). This is a staging-hygiene gate, not a code
   defect — the code itself is approved.
