# Review — task whatsapp-b2b-lead-bridge (Group 3)

**Verdict:** APPROVED

## Verification performed (independent, not from the implementer's report)

1. Read `apps/backend/services/crm_service.py:538-558` directly: `advance_lead()` diff
   (`git diff`) confirms the extension is exactly additive — new `lead_type: Optional[str] = None`
   kwarg, default preserves the prior single-write body 1:1 (`patch = {"stage": stage}`, merges
   `lead_type` into the same patch dict only if not None, single `.update(patch)` call — no second
   Supabase query). `whatsapp_intake()` (`crm_service.py:496`) is untouched.
2. Read `apps/backend/services/taty_lead_router.py:373-380`: the new `business_interest` branch
   calls `service.advance_lead(lead_id, current_stage, lead_type="business_interest")` — passing
   the lead's own current stage back, guarded by `if current_stage is not None`. No independent
   Supabase write added to this file. Execution falls through to the shared Taty reply generation
   below (no early `return` in this branch) — confirmed by reading the surrounding code.
3. Read the four new tests in `test_taty_lead_router.py:200-266` and confirmed they assert the
   exact required behaviors: new lead → `advance_lead("lead-1", "NUEVOS", lead_type=...)`;
   existing lead reclassified → single `advance_lead` call, `whatsapp_intake` never called (no
   duplicate row); non-business message → no call anywhere carries a `lead_type` kwarg (previously
   set `lead_type` untouched); stage-preservation test asserts `advance_lead` is called with the
   *same* stage it read, never a different one.
4. Ran the tests myself (not trusting the report): `py -3.11 -m pytest tests/test_crm_service.py
   tests/test_taty_lead_router.py -q` → `60 passed, 4 skipped` — matches the report exactly. The
   4 skips are the documented py311-only baseline (MEMORY.md), unrelated to this change.
5. `git diff --stat` / `git status --porcelain` confirm scope: only `crm_service.py`,
   `taty_lead_router.py`, and `test_taty_lead_router.py` changed for this task. `apps/chatwoot-
   bridge/` has zero diff. Migration `0049_crm_leads_lead_type.sql` exists as an untracked file
   (from Group 2, already reviewed separately) but was not modified or applied by this task — no
   DB write for `lead_type` is possible without it, and the code fails safe (Supabase would reject
   the unknown column) until the founder approves applying it.

## Checkpoints
- C1 (reuses existing write path, no independent Supabase query): [x]
- C2 (exact behavior: create/update/no-clear/stage-untouched): [x]
- C3 (additive signature extension, no caller regression): [x] — `whatsapp_intake` untouched;
  `advance_lead`'s only other callers (`sales_interest`/`payment_confirmation` branches, plus
  `test_crm_service.py`) call it positionally with 2 args, unaffected by the new optional kwarg.
- C4 (zero regression in preexisting + Group 1 tests): [x] — 60 passed, 4 pre-existing skips, no
  new failures, no test edited.
- C5 (nothing out of scope touched): [x] — `chatwoot-bridge/` and `tasks.md` untouched by this
  task; migration file present but not applied (Group 2's responsibility, not re-applied here).

## Required changes
None.
