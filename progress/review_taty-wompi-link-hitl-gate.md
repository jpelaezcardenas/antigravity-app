# Review — task taty-wompi-link-hitl-gate

**Verdict:** APPROVED

**Reviewer:** claude-sonnet-4-6
**Date:** 2026-08-30

## Checkpoints

- C1: [x] `_enqueue_wompi_link_approval` is a plain `def` (sync) — `taty_lead_router.py:138`. Matches existing local-helper convention and design.md Decision 1.
- C2: [x] `route_lead_message` sales_interest branch (line 363) calls only `_enqueue_wompi_link_approval`. `generate_wompi_link` is never called there. Verified visually.
- C3: [x] Reply at lines 367–372: "¡Con gusto te ayudo! Un asesor de Contexia va a validar tu caso..." — no amount, no link, no merchant name. Decision 4 satisfied.
- C4: [x] `payload={"lead_id": lead_id}` is the sole payload in the insert (taty_lead_router.py:160). Decision 5 satisfied.
- C5: [x] `approve_draft` at line 199–200 branches on `wompi_payment_link` and awaits `_deliver_wompi_link` directly — no executor_outbox indirection. Decision 2 satisfied.
- C6: [x] `_deliver_wompi_link` (approval_queue_service.py:299) has an explicit "Never raises" contract with its own inner try/except. Outer approval already committed to DB before the call. Decision 3 satisfied. Test `test_delivery_failure_does_not_undo_the_approval` confirms this.
- C7: [x] `tenant_id` is read from `crm_leads` for the lead (taty_lead_router.py:151–153) and passed into the `approval_queue` insert explicitly. `NOT NULL` constraint satisfied (Migration 0033, Decision #14).
- C8: [x] Tests in `test_taty_lead_router.py::TestEnqueueWompiLinkApproval` and `test_approval_queue_service_wompi_link.py` cover: enqueue insert called, `generate_wompi_link` NOT called, reply has no checkout URL, approve→generate+send, missing phone→skips send without failing, send failure→`success=True`/`status=APPROVED`, other draft types (tax_correction) unaffected.
- C9: [x] 50 tests green, 0 failed (reported 2026-08-30 in impl file).
- C10: [x] ARCHITECTURE.md docs-sync: no new container or external dependency added. `approval_queue` already documented under Decision #14. No ARCHITECTURE.md update required.
- C11: [ ] Stage 11 (deploy to production): tasks 4.1–4.4 marked `[ ]` — not yet complete. This is expected at review time; deploy is the next step after this review.

## Notes

One theoretical edge case: if `_deliver_wompi_link` somehow raises despite its explicit "Never raises" design, the outer `except Exception` in `approve_draft` (line 208) would return `False, None, str(e)` even though the DB row was already set to APPROVED at line 181. This is structurally identical to the vectorization path that already exists in the same function and is consistent with the codebase convention. Not a blocker — the method is designed not to raise and is tested against failure paths.

## Required changes

None. Code, tests, and design decisions are fully aligned.

## Next steps (not blocking this approval)

1. Stage 11: commit + push to `main`, verify Railway deploy, run manual smoke test (task 3.2), create deployment report (task 4.4).
2. Founder action 5.1: resolve merchant-of-record (Wompi account for Entidad A) — tracked in tasks.md, out of scope for this change.
