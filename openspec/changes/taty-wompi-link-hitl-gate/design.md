## Context

`route_lead_message` is a plain synchronous function, deliberately: every existing helper in
`taty_lead_router.py` (`_get_lead_stage`, `get_lead_phone`, `_create_empty_tax_profile`,
`_get_latest_transaction`) talks to Supabase directly with small sync functions rather than
delegating to other services' async methods, specifically so the router stays trivially unit
testable with no event-loop ceremony. `ApprovalQueueService`, by contrast, is `async` throughout
(it's called from async FastAPI endpoints). Wiring the two together without breaking either
convention is the one real design decision here.

## Decisions

1. **Enqueue with a local sync helper, not `ApprovalQueueService.enqueue_draft`.**
   `route_lead_message` stays synchronous — calling an `async def` service method from it would
   require either making `route_lead_message` itself async (touching its one real caller and
   ~10 existing synchronous test call sites for no behavioral benefit) or calling `asyncio.run()`
   from inside a function that FastAPI already invokes from within a running event loop, which
   raises. A small sync helper doing `client.table("approval_queue").insert(...)` directly matches
   the file's own established pattern exactly and touches nothing outside this file.
   *Alternative considered:* make `route_lead_message` async. Rejected — it is a deterministic
   classifier with no genuine I/O-latency reason to be async; the only reason would be this one
   call, and the sync helper removes that reason entirely.

2. **The real send happens inside `approve_draft`, synchronously, at approval time.**
   `approve_draft` already branches on `draft_type` for `tax_correction` (creating an
   `executor_outbox` job — a *deferred*, polled side effect). A `wompi_payment_link` approval does
   not need that indirection: a human just took the approval action inside an already-async
   request handler, so generating the link and calling `send_whatsapp_message` right there is
   simpler and has no consistency benefit from being deferred.
   *Alternative considered:* route through `executor_outbox` like `tax_correction`, for
   consistency. Rejected for now — that requires locating and verifying whatever currently polls
   `executor_outbox`, which is unrelated scope; a direct synchronous send is correct and simpler.
   Revisit only if a real need for retry/backoff on the WhatsApp send emerges.

3. **A failed delivery does not roll back the approval.** Mirrors the existing convention (a
   failed vectorization does not un-approve a `tax_correction`). The human's decision to approve
   was correct at the time it was made; a downstream WhatsApp API failure is an operational
   problem to retry or handle manually, not a reason to pretend the approval never happened.

4. **The customer-facing reply on `sales_interest` says an advisor will follow up — no amount, no
   link, no merchant name.** Anything more specific risks stating a number or an entity before a
   human has actually decided one applies to Ley 1480 art. 29's rule that advertised specific
   conditions become binding on the advertiser.

5. **`payload={"lead_id": lead_id}` is the entire contract.** `get_lead_phone`/`generate_wompi_link`
   are both already keyed on `lead_id` and re-read current state at approval time (not the state
   at enqueue time) — deliberately, since a lead's phone or stage could change in the interval
   between a customer's message and an advisor's review, and re-reading is strictly safer than
   trusting a stale snapshot.

## Risks / Trade-offs

- **[Risk] A human must now be watching the approval queue for this WhatsApp sales flow to
  function at all** — previously fully automatic, now blocked until reviewed. → **Mitigation**:
  this is the explicit point of the change; the founder requested it after a live scare. Revisit
  once the merchant-of-record question (out of scope here) is resolved, and consider re-automating
  for the correctly-owned Wompi account with a lighter-weight check.
- **[Trade-off] No dedicated review UI for this draft type.** The generic approval-queue surface
  already used for `tax_correction` works (same table, same list/approve/reject endpoints), just
  without WhatsApp-specific framing (customer name, message, amount) in the UI today. Acceptable
  for an urgent safety fix; a follow-up can improve the review experience specifically.

## Migration Plan

1. Land the enqueue-side change (`taty_lead_router.py`) and the approval-side change
   (`approval_queue_service.py`) together — one is inert without the other, so there is no
   safe intermediate state to deploy separately.
2. Rollback: revert both files. `generate_wompi_link` and `send_whatsapp_message` are both
   unmodified, so reverting restores the exact prior (automatic, ungated) behavior.
