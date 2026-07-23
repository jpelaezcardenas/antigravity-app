# Review — task chatwoot-hermes-taty-bridge-task1 (Task Group 1: Backend CRM WhatsApp Intake)

**Verdict:** APPROVED

## Scope validated

Task Group 1 only (tasks 1.1–1.4): `apps/backend/tests/test_crm_whatsapp_intake.py` (new),
`apps/backend/services/crm_service.py`, `apps/backend/presentation/crm_endpoints.py`.
Groups 2–15 (existing-test review, DB-state report, curl verification, the bridge itself,
Chatwoot compose, docs, deploy, final review gate) are explicitly out of scope per the
implementer's report and per the harness "one task at a time" rule — not evaluated here.

## Spec conformance (`specs/crm-b2c-sell-machine/spec.md`)

- Scenario "new phone creates a lead": `crm_service.py:387-417` inserts `stage: "NUEVOS"` and
  returns `is_new: True` when `.maybe_single()` returns no row. Matches.
- Scenario "known phone found, not duplicated": returns existing `lead_id`/`stage`,
  `is_new: False`, `leads_table.insert.assert_not_called()` verified in test. Matches.
- Scenario "requires tenant-scoped auth, no row read/written on rejection": endpoint relies on
  the router-level `dependencies=[Depends(get_current_user)]` (`crm_endpoints.py:17`, unchanged),
  which raises 401 before the route body runs when `settings.AUTH_ENFORCED = True` and no valid
  token is present (`core/deps.py:53-80`). Test asserts `mock_get_service.return_value
  .whatsapp_intake.assert_not_called()` — i.e., the service (and therefore Supabase) is never
  touched. Matches.

## Tenant-scoping / auth-contract check (design.md decision 6 context)

- `whatsapp_intake` genuinely reuses `_resolve_cliente_cero_tenant_id` (`crm_service.py:99-107`)
  — the exact same helper `b2c_pipeline`/`advance_lead` call, not a parallel/weaker mechanism.
  Confirmed by reading the method body, not just the report's claim.
- The lookup is scoped by **both** `tenant_id` and `whatsapp_phone`
  (`.eq("tenant_id", tenant_id).eq("whatsapp_phone", normalized_phone)`,
  `crm_service.py:398-403`) — not phone-only, so it cannot leak a lead across tenants. This is
  stricter than the pre-existing `find_or_create_lead()` in
  `apps/backend/services/taty_lead_router.py:246-278` (Change D), which looks up by
  `whatsapp_phone` alone with **no tenant filter** on the read (only sets `tenant_id` on
  insert). That's a pre-existing, out-of-scope function this task did not touch — flagging as
  an observation, not a blocker: a future change should reconcile the two find-or-create paths
  (this new one is the stricter/better pattern) rather than let them diverge further.
- `.maybe_single()` is safe here: `crm_leads` has `CONSTRAINT uq_crm_leads_tenant_phone UNIQUE
  (tenant_id, whatsapp_phone)` (`migrations/0022_crm_b2c_sell_machine.sql:21`), so a
  `(tenant_id, whatsapp_phone)` lookup can never return more than one row — `.maybe_single()`
  degrading to `None` on zero rows (as mocked/asserted in the tests) is the correct, safe
  behavior and matches the existing `get_tax_profile` 0-row-safe precedent cited in the report.
- Note (non-blocking): `_resolve_cliente_cero_tenant_id` ignores the caller's own
  `resolved_tenant_id` from the JWT and always resolves the Cliente Cero tenant — this is
  consistent with every other method in `CrmService` (`b2b_payments_grid`, `b2c_pipeline`,
  `advance_lead`, etc.), so it is not a new deviation. It does mean the spec's "tenant-scoped to
  the calling caller's tenant" phrase is satisfied only in the narrow sense of "the app's one
  real tenant, resolved server-side" rather than trusting a caller-supplied tenant claim — same
  limitation the rest of the codebase already has, not introduced by this task.

## Standards check

- Full type hints on `_normalize_whatsapp_phone(whatsapp_phone: str) -> str` and
  `whatsapp_intake(self, whatsapp_phone: str) -> Dict[str, Any]`. English-only comments/names.
- No hardcoded secrets.
- No unrelated refactoring: `git diff --stat main` shows only additive lines in the two touched
  files (11 + 39 lines) plus the new test file plus the (already-present-on-branch) `tasks.md`.
- TDD claim is plausible: the tests patch `services.crm_service.get_service_supabase` and call
  `CrmService().whatsapp_intake(...)`, a method that did not exist before this diff — running
  those tests pre-implementation would `AttributeError`, and the endpoint tests would 404 pre-
  route-registration, consistent with the report's stated 4-failed/1-passed red baseline.

## Test re-run

```
python -m pytest apps/backend/tests/test_crm_whatsapp_intake.py apps/backend/tests/test_crm_service.py \
  apps/backend/tests/test_crm_service_b2b_writes.py apps/backend/tests/test_crm_endpoints.py \
  apps/backend/tests/test_crm_b2c_endpoints.py -v
```
Result: **26 passed, 4 skipped** — exact match to the implementer's report (5/5 new tests pass;
4 pre-existing skips in `test_crm_service.py`, unrelated to this change).

## Checkpoints (scoped to Task Group 1 — full-change/deploy checkpoints not applicable yet)

- Spec scenarios implemented and tested: [x]
- Tenant-scoping reuses existing helper (no parallel/weaker mechanism): [x]
- Tests genuinely assert real outcomes (insert payload contents, `is_new`, `assert_not_called`),
  not just "no exception": [x]
- No fabricated stubs / no disabled type-checking / no hand-edited `app/`: [x]
- `./init.sh` / targeted pytest green: [x] (ran targeted suite above; full `RUN_TESTS=1 bash
  init.sh` is reserved for the change's final review gate, task 15.2, not this task group)
- Docs-sync (ARCHITECTURE.md container/dependency change): N/A for this task — no new container,
  the endpoint is added to the existing Railway-deployed backend; ARCHITECTURE.md update for the
  Chatwoot/bridge containers is correctly deferred to task 13.1 of this same change.

## Required changes (non-blocking, to close out before Task Group 1 is marked done in tasks.md)

1. `openspec/changes/chatwoot-hermes-taty-bridge/tasks.md` items 1.1–1.4 are still `[ ]` even
   though the report and this review confirm they're complete — check them off (`[x]`) so the
   change's own task tracker reflects reality before the next task group starts.

## Notes for a future change (not blocking this task)

- Consider reconciling `CrmService.whatsapp_intake` (tenant-scoped) with the pre-existing
  `taty_lead_router.find_or_create_lead` (phone-only, no tenant filter on read) so WhatsApp
  intake has a single source of truth rather than two diverging find-or-create paths against the
  same table/column.
