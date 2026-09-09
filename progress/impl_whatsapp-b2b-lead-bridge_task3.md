# Implementer report — whatsapp-b2b-lead-bridge, Task Group 3

**Task:** 3.1 / 3.2 / 3.3 — Wire `lead_type` write into `route_lead_message`

## Files touched

1. `apps/backend/services/crm_service.py`
   - `CrmService.advance_lead()` extended additively with an optional `lead_type: Optional[str] = None`
     parameter (default preserves the exact prior behavior for every existing caller that omits it).
     When provided, it is merged into the same `crm_leads` update patch alongside `stage` — no second
     Supabase write. Docstring explains the "pass the lead's own current stage back" convention used
     to set `lead_type` without advancing/regressing the funnel stage.

2. `apps/backend/services/taty_lead_router.py`
   - `route_lead_message()`: added a new `if intent == "business_interest":` block, placed right after
     the persona-fields persistence and before the `sales_interest` branch. When `current_stage is not
     None`, it calls `service.advance_lead(lead_id, current_stage, lead_type="business_interest")` —
     reusing the extended `advance_lead`, no independent Supabase query added to this file. Execution
     falls through to the existing bottom-of-function Taty handoff (`unknown`-style reply generation),
     unchanged — this branch only adds the side effect, never a return.

3. `apps/backend/tests/test_taty_lead_router.py`
   - New `TestRouteLeadMessageBusinessInterestLeadType` class (inserted before
     `TestRouteLeadMessageReturnsClassificationForAutoTagging`), covering the four scenarios required
     by 3.1:
     - `test_new_lead_business_interest_sets_lead_type_on_creation` — stage `NUEVOS` (fresh lead),
       asserts `advance_lead("lead-1", "NUEVOS", lead_type="business_interest")`.
     - `test_existing_lead_reclassified_business_interest_updates_no_duplicate` — stage
       `PROSPECTOS`, asserts a single `advance_lead` call (update, not create) and
       `whatsapp_intake` never called from this path.
     - `test_non_business_message_does_not_clear_lead_type` — a plain `"unknown"`-intent message;
       asserts no `advance_lead` call anywhere carries a `lead_type` kwarg, i.e. a previously-set
       `lead_type` is left untouched.
     - `test_business_interest_never_advances_or_regresses_stage` — stage `LISTOS_CONTADORA`
       (deep in the funnel), asserts `result["stage"]` is unchanged and `advance_lead` is called with
       that same stage back, never a different one.

## Test command and output

```
cd apps/backend
py -3.11 -m pytest tests/test_crm_service.py tests/test_taty_lead_router.py -q
```

```
ssss............................................................         [100%]
60 passed, 4 skipped, 20 warnings in 84.75s (0:01:24)
```

(The 4 skips are the pre-existing `test_crm_service.py` skips documented in
`MEMORY.md` — "Backend pytest interpreter + baseline" — unrelated to this change; only py311 has
pytest, and this baseline was confirmed unaffected.)

## Regression confirmation

- Full `test_taty_lead_router.py` suite (60 tests, including Group 1's `business_interest`
  classifier tests, the pre-existing `sales_interest`/`payment_confirmation`/`unknown` branch
  tests, `TestFindOrCreateLead`, `TestEnqueueWompiLinkApproval`, `TestGenerateWompiLink`,
  `TestVerifyWompiTransaction`, `TestRouteLeadDocument`, etc.) passes green — no changes to any
  existing test, no new failures introduced by the `advance_lead` signature extension or the new
  `business_interest` branch.
- `test_crm_service.py` passes green (4 pre-existing skips, no new skips/failures) — confirms
  `advance_lead`'s additive extension did not break any of its existing callers/assertions
  (e.g. `sales_interest`/`payment_confirmation` branches still call `advance_lead(lead_id, stage)`
  positionally with no `lead_type` kwarg, exactly as before).

## Scope notes

- Did not touch `tasks.md`.
- Did not touch `apps/chatwoot-bridge/` (Group 4).
- Did not apply migration `0049_crm_leads_lead_type.sql` — left as-is (Group 2, not applied,
  requires founder confirmation per repo convention).
- No independent/raw Supabase query was added to `taty_lead_router.py` — the only write is
  through the now-extended `CrmService.advance_lead()`.
