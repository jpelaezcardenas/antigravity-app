# Review — task whatsapp-b2b-lead-bridge (Task 1: Classifier: add `business_interest` category)

**Verdict:** APPROVED

## Verification performed independently

1. **Ordering (design.md Decision #2).** Read `apps/backend/services/taty_lead_router.py:106-123`
   directly. `classify_lead_intent()` checks `PAYMENT_CONFIRMATION_KEYWORDS` first (line 116),
   then the new `BUSINESS_INTEREST_KEYWORDS` (line 118), then `SALES_INTEREST_KEYWORDS` (line 120).
   Matches design.md Decision #2 exactly: payment confirmation is never masked by a business
   keyword, and business_interest is checked before sales_interest.

2. **Zero regression on existing fixtures.** Confirmed `SALES_INTEREST_KEYWORDS` and
   `PAYMENT_CONFIRMATION_KEYWORDS` tuples are untouched (same literal values as before the diff —
   `git diff` shows only additions, no line inside those two tuples changed). The 3 original tests
   (`test_sales_interest_detected`, `test_payment_confirmation_detected`, `test_unknown_falls_back`)
   are present unmodified, plus 3 new explicit regression-pin tests with the same assertions
   (`test_sales_interest_still_detected_unchanged`, etc.) — redundant but harmless, not a defect.

3. **New tests are TDD-legitimate.** Read `test_taty_lead_router.py:30-84`. Every
   `TestClassifyLeadIntent` test calls `classify_lead_intent()` directly with a literal message
   string and asserts on its real return value — no mock/patch touches the function under test or
   its keyword tuples. The priority test
   (`test_payment_confirmation_takes_priority_over_business_interest`, line 62) uses a message
   containing both a payment keyword ("Ya pagué, listo") and a business keyword ("Somos una SAS")
   and asserts `payment_confirmation` wins — this is a real behavioral assertion of the precedence
   rule, not a tautology.

4. **Scope discipline.** `git status`/`git diff --stat` confirms `crm_leads` migrations,
   `route_lead_message()`'s write path, and `apps/chatwoot-bridge/main.py` are untouched by this
   diff. Other dirty files in the working tree (`plan_features.py`, `hermes-hubspot-poller/*`,
   `0046_gmail_sender_map.sql`, `feature_list.json`, `contexia-app/components/*`) are pre-existing
   uncommitted changes from prior sessions/tasks, unrelated to and not touched by this task's diff
   — confirmed by inspecting their diffs, which have no relation to `taty_lead_router.py` or its
   tests.

5. **Tests run independently, py311 interpreter (only interpreter with pytest in this repo per
   project memory):**
   ```
   cd apps/backend && py -3.11 -m pytest tests/test_taty_lead_router.py -q
   ```
   Result: `56 passed, 20 warnings in 96.95s` — full module green, including
   `TestRouteLeadMessage` and all other classes (no regression from the new branch).

## Checkpoints (Task 1 only — 1.1/1.2/1.3 of tasks.md)
- 1.1 (failing tests written first, per report) — [x] plausible from report; final state has all
  tests passing and covering the required cases (business-shaped messages, unchanged existing
  fixtures, payment-vs-business priority).
- 1.2 (`BUSINESS_INTEREST_KEYWORDS` + 4th branch, correct order) — [x] verified directly in code.
- 1.3 (tests green) — [x] verified independently (56 passed).

## Notes (non-blocking)
- Keyword `"sas"` is a bare substring match (`"sas" in message_lower`), same pattern as existing
  lists. No false positive found in the current fixture set, but this is a latent risk the
  design.md itself flagged and explicitly deferred to human review via tagging rather than
  auto-action — acceptable per Decision's stated mitigation, not a defect in Task 1's scope.
- Task 1 does not mark checkboxes in `tasks.md` — that remains the leader's job per HARNESS.md,
  not a Task 1 defect.

## Required changes
None.
