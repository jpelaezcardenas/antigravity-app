# Implementation report — Task 1: Classifier: add `business_interest` category

**Change:** whatsapp-b2b-lead-bridge
**Task:** 1.1 / 1.2 / 1.3 (Group 1 only — no other groups touched)

## Files touched

1. `apps/backend/tests/test_taty_lead_router.py`
   - `TestClassifyLeadIntent` class extended with:
     - `test_business_interest_detected` (parametrized, 6 business-shaped messages: "Somos una
       SAS...", "Tengo mi empresa...", "Mi negocio...", "Somos una sociedad...", "Buscamos
       contabilidad para mi compañía", "Somos una persona jurídica...") — asserts
       `intent == "business_interest"`.
     - `test_payment_confirmation_takes_priority_over_business_interest` — a message with both a
       payment keyword ("Ya pagué, listo") and a business keyword ("Somos una SAS") — asserts
       `payment_confirmation` wins.
     - `test_sales_interest_still_detected_unchanged`, `test_payment_confirmation_still_detected_unchanged`,
       `test_unknown_still_falls_back_unchanged` — regression pins for the three existing branches
       (in addition to the original `test_sales_interest_detected` /
       `test_payment_confirmation_detected` / `test_unknown_falls_back`, left untouched).

2. `apps/backend/services/taty_lead_router.py`
   - Added `BUSINESS_INTEREST_KEYWORDS` tuple right after `PAYMENT_CONFIRMATION_KEYWORDS`
     (line ~75-88): `"sas"`, `"empresa"`, `"negocio"`, `"sociedad"`, `"compañía"`, `"compania"`,
     `"persona jurídica"`, `"persona juridica"`.
   - In `classify_lead_intent()` (was lines 91-106), added a 4th branch checked **after**
     `payment_confirmation` and **before** `sales_interest`:
     ```python
     if any(keyword in message_lower for keyword in PAYMENT_CONFIRMATION_KEYWORDS):
         return "payment_confirmation", 0.9
     if any(keyword in message_lower for keyword in BUSINESS_INTEREST_KEYWORDS):
         return "business_interest", 0.8
     if any(keyword in message_lower for keyword in SALES_INTEREST_KEYWORDS):
         return "sales_interest", 0.8
     return "unknown", 0.0
     ```
   - Updated the function's docstring return-type comment to list `"business_interest"` among the
     possible intents.

## Scope discipline

Did not touch: `crm_leads` schema/migrations (Group 2), `route_lead_message()`'s write path
(Group 3), `apps/chatwoot-bridge/main.py` (Group 4), or `tasks.md` (leader's job after review).

## Test command and output

Interpreter: `py -3.11` (per project memory — only py311 has pytest installed in this repo).

```
cd apps/backend
py -3.11 -m pytest tests/test_taty_lead_router.py -q
```

Result:
```
........................................................                 [100%]
56 passed, 20 warnings in 85.47s (0:01:25)
```

All 56 tests in the module pass, including:
- the 3 pre-existing `TestClassifyLeadIntent` tests (unchanged assertions),
- the 6 new parametrized `business_interest` cases,
- the payment-vs-business priority test,
- the 3 new explicit regression-pin tests,
- all `TestRouteLeadMessage` and other classes in the file (sales_interest / payment_confirmation
  / Wompi / persona-field tests) — no regression from the new branch.

No deviation from the task spec. Keyword `"sas"` deliberately matches as a substring (e.g. inside
"casa" would NOT match since it's a standalone lowercase substring check like the existing
keyword lists — verified no false positive appears in any existing sales_interest/payment_confirmation/
unknown fixture in the suite).
