## 1. Gate the sales-interest branch behind approval_queue

- [ ] 1.1 Write failing tests in `test_taty_lead_router.py`: a `sales_interest` message inserts an
      `approval_queue` row (`draft_type="wompi_payment_link"`, `payload={"lead_id": ...}`,
      correct `tenant_id`), does NOT call `generate_wompi_link`, and the reply contains no
      checkout URL / amount.
- [ ] 1.2 Update the 3 existing tests that currently assert the opposite (`generate_wompi_link`
      called, link present in reply) to match the new behavior.
- [ ] 1.3 Add `_enqueue_wompi_link_approval(lead_id)` to `taty_lead_router.py` — sync helper,
      direct Supabase insert, matching the file's existing local-helper convention (not
      `ApprovalQueueService.enqueue_draft`, which is async — see design.md Decision 1).
- [ ] 1.4 Replace the `sales_interest` branch's direct `generate_wompi_link` call with the new
      helper; change the customer-facing reply to say an advisor will follow up (no link, no
      amount, no merchant name — design.md Decision 4).
- [ ] 1.5 Tests green.

## 2. Deliver the real link only on approval

- [ ] 2.1 Write failing tests in a new `test_approval_queue_service_wompi_link.py`: approving a
      `wompi_payment_link` draft calls `generate_wompi_link(lead_id)` and awaits
      `send_whatsapp_message(phone, ...)` with the generated link in the text; rejecting sends
      nothing; a `send_whatsapp_message` failure still leaves the decision `approved`.
- [ ] 2.2 Add the `wompi_payment_link` branch to `ApprovalQueueService.approve_draft` (sibling to
      the existing `tax_correction` branch), reading `lead_id` from `decision.payload`.
- [ ] 2.3 Tests green.

## 3. Verify

- [ ] 3.1 `RUN_TESTS=1 bash init.sh` green; full backend suite shows no new regressions vs the
      known 40 pre-existing failures.
- [ ] 3.2 Manual smoke test against production: send a real `sales_interest` message, confirm no
      link arrives automatically, confirm a `pending_approval` row exists, approve it via the
      approval-queue API, confirm the link then arrives on the real phone.

## 4. Stage 11 — Deploy to Production (MANDATORY)

- [ ] 4.1 git commit + push to `main`
- [ ] 4.2 Railway deploy healthy
- [ ] 4.3 Production verification per 3.2
- [ ] 4.4 Create report: `openspec/changes/taty-wompi-link-hitl-gate/reports/YYYY-MM-DD-deployment.md`

## 5. FOUNDER ACTION — out of scope here, tracked so it is not lost

- [ ] 5.1 Decide and execute the merchant-of-record fix: set up/verify a Wompi account for
      Entidad A and repoint `WOMPI_PUBLIC_KEY`/`WOMPI_PRIVATE_KEY` (or equivalent) once ready.
      This change's HITL gate is a safety brake, not a substitute for that decision.

## 6. Archive

- [ ] 6.1 Sync the capability into `openspec/specs/` and archive.
