# impl: taty-wompi-link-hitl-gate (Sections 1-3)

**Date:** 2026-08-30
**Implementer:** claude-sonnet-4-6

## Status: complete — awaiting reviewer

## Files touched

- `apps/backend/services/taty_lead_router.py` — `_enqueue_wompi_link_approval` helper (sync
  Supabase insert); `sales_interest` branch replaced direct `generate_wompi_link` call with
  `_enqueue_wompi_link_approval`; reply changed to advisor-will-follow-up (no link, no amount,
  no merchant name).
- `apps/backend/services/approval_queue_service.py` — `wompi_payment_link` branch added to
  `approve_draft` (calls `_deliver_wompi_link`); `_deliver_wompi_link` static method added:
  reads lead phone, calls `generate_wompi_link`, awaits `send_whatsapp_message`; delivery
  failure logged but does not revert the approval.
- `apps/backend/tests/test_taty_lead_router.py` — `TestEnqueueWompiLinkApproval` class added;
  existing `sales_interest` tests updated to assert `_enqueue_wompi_link_approval` called and
  `generate_wompi_link` NOT called, reply has no checkout URL.
- `apps/backend/tests/test_approval_queue_service_wompi_link.py` — new file; 4 tests covering:
  approval generates and sends the link, missing phone skips send without failing approval,
  delivery failure does not undo approval, other draft types unaffected.

## Test output

```
tests/test_taty_lead_router.py — 46 passed
tests/test_approval_queue_service_wompi_link.py — 4 passed

============================== 50 passed, 20 warnings in 76.35s ===============
```

All 50 tests green. No regressions in the two target test files.

## Key design decisions implemented

1. `route_lead_message` stays synchronous — `_enqueue_wompi_link_approval` is a plain sync
   Supabase insert, matching the file's existing local-helper convention.
2. Real link delivery happens only inside `ApprovalQueueService.approve_draft` → `_deliver_wompi_link`.
3. A WhatsApp send failure logs an error but does not revert the `approved` decision.
4. Customer reply on `sales_interest`: "Un asesor de Contexia va a validar tu caso..." — no
   link, no amount, no merchant name.
