# Review — task taty-lead-router-tenant-scoping (Task Groups 1-2)

**Verdict:** APPROVED

## Verification performed

1. **`whatsapp_intake`'s `full_name` scope** (`apps/backend/services/crm_service.py:387-427`): confirmed
   by direct read. `full_name` is only referenced once, at line 420 (`"full_name": full_name or
   whatsapp_phone`) inside the `insert(...)` payload. The lookup path (lines 402-412,
   `.select("id, stage").eq("tenant_id", tenant_id).eq("whatsapp_phone", normalized_phone).maybe_single()`)
   never touches `full_name` and returns before the insert block runs when a row is found. Matches
   design.md Decision 2 exactly.

2. **`find_or_create_lead` delegation** (`apps/backend/services/taty_lead_router.py:246-255`): confirmed
   via `git diff` — the old direct `crm_leads` lookup query and the old inline `tenants` /
   `is_cliente_cero` tenant-resolution query are both fully deleted (net -29/+6 lines), replaced by a
   single `get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)["lead_id"]`. Grepped
   the rest of the file: the only remaining `get_service_supabase()`/`crm_leads` references are
   `_get_lead_stage`, `_get_lead_phone`, `_get_latest_transaction`, and `_create_empty_tax_profile` —
   none of these are reachable from `find_or_create_lead`; they belong to `route_lead_message`/
   `route_lead_document`, which are explicitly out of scope and were confirmed untouched by `git diff`.
   One minor, harmless behavior note: the old insert set `"source": "whatsapp"` explicitly; the new
   path (via `whatsapp_intake`) omits it, but `crm_leads.source` has `DEFAULT 'whatsapp'`
   (`apps/backend/migrations/0022_crm_b2c_sell_machine.sql:15`), so this is not an observable
   regression.

3. **Test genuineness**: `TestFindOrCreateLead`'s two rewritten tests
   (`test_taty_lead_router.py:477-510`) patch `services.taty_lead_router.get_crm_service` and assert
   `whatsapp_intake` is called with the correct phone/`full_name` and that `find_or_create_lead`
   returns the mocked `lead_id` — this genuinely exercises the delegation, not just "no exception."
   `test_crm_whatsapp_intake.py`'s 3 new cases (`:69`, `:95`, `:121`) each assert on the actual
   `insert()`/lookup call args (`full_name` set correctly on create-with-name,
   fallback-to-phone-on-create-without-name, and `insert.assert_not_called()` +
   `full_name` correctly ignored on the existing-row path) — real assertions on outcomes, not stubs.

4. **Targeted re-run** (`cd apps/backend && python -m pytest tests/test_crm_whatsapp_intake.py
   tests/test_taty_lead_router.py tests/test_whatsapp_endpoints.py -v`): reproduced independently —
   **58 passed**, 0 failed, 20 warnings (pre-existing pydantic/multipart deprecations).

5. **Full-suite pre-existing-failure comparison** (independently executed, not trusted from the
   report):
   - With this diff applied: `pytest tests -v --ignore=tests/test_profile_support.py
     --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py` →
     **40 failed, 588 passed, 109 skipped** (259.4s).
   - `git stash push` on exactly the 4 changed files (`crm_service.py`, `taty_lead_router.py`,
     `test_crm_whatsapp_intake.py`, `test_taty_lead_router.py`) to get back to the unmodified branch
     tip, same command re-run: **40 failed, 585 passed, 109 skipped** (281.8s).
   - The 40 failed test names are byte-identical between both runs (`test_approval_rules_stage3_4`,
     `test_approval_rules_stage8_11` x7, `test_centinela_alerts_get`, `test_model_selector_cloud_only`,
     `test_secure_llm`, `test_shadow_gl_integration` x2, `test_shadow_gl_siigo_csv` x11,
     `test_shadow_gl_stage1_migration` x3, `test_shadow_gl_stage4_uploader` x2,
     `test_shadow_gl_stage5_error_handling`, `test_shadow_gl_stage8_e2e` x7,
     `test_wizard_auditoria_sombra` x2). The only difference is 588 vs 585 passed, exactly the 3 new
     tests this change adds to `test_crm_whatsapp_intake.py`. **Confirmed: all 40 failures are
     pre-existing on the branch tip and not introduced by this diff.** `git stash pop` restored the
     diff afterward; `git status` confirmed a clean restore (same 4 modified files as before the
     stash).

6. **Scope confirmation**: `git diff -- apps/backend/services/taty_lead_router.py` shows the *only*
   hunk touches `find_or_create_lead` (lines 246-255); `route_lead_message`/`route_lead_document` are
   untouched in the diff. `git diff --stat` confirms no changes under `apps/chatwoot-bridge/` or
   `openspec/changes/taty-lead-router-tenant-scoping/tasks.md`.

## Checkpoints (design.md decisions / spec.md MODIFIED requirement)

- Decision 1 (thin delegating wrapper, not a parallel rewrite): [x] — verified in code.
- Decision 2 (`full_name` optional, insert-path only): [x] — verified in code.
- Decision 3 (signature/return type preserved exactly, `whatsapp_endpoints.py` untouched): [x] —
  confirmed no changes to that file; signature matches `find_or_create_lead(whatsapp_phone: str,
  full_name: Optional[str] = None) -> str`.
- Decision 4 (tests rewritten to mock `get_crm_service`, not `get_service_supabase`): [x] — verified.
- spec.md MODIFIED requirement (tenant_id AND whatsapp_phone keyed lookup, single implementation via
  `CrmService.whatsapp_intake`): [x] — `whatsapp_intake`'s lookup filters on both `tenant_id` and
  `whatsapp_phone` (crm_service.py:405-406); `find_or_create_lead` no longer runs an independent
  query.
- No scope creep into `route_lead_message`/`route_lead_document`/`chatwoot-bridge`/`tasks.md`: [x].
- Full backend suite green modulo pre-existing failures, verified independently via stash comparison:
  [x].

## Required changes

None.
