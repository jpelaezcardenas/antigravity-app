# Deployment report — taty-kb-and-react-router

Date: 2026-07-20

## Summary

Change deployed and verified live in production. Taty's `unknown`-intent fallback now runs a
bounded Reason→Act→Reason loop (classify → KB search → synthesize) instead of returning a static
non-answer, closing gaps #3 (bounded ReAct, scoped narrowly — see design.md Decision 1) and #4
(`retrieve_similar` finally wired into the lead router) from the plan-vs-build audit.

## Commits deployed

- `98d4632` — feat(taty): KB-grounded fiscal answers for the unknown-intent fallback

## Stage 11 steps executed

1. Merged `feature/taty-kb-and-react-router` to `main` (fast-forward, confirmed via
   `git merge-base`), pushed. Railway deploy `756cd369` reached `SUCCESS`.
2. **A real, pre-existing gap was discovered while preparing the live smoke test (not fixed in
   this change — deliberately out of scope, see below)**: `route_lead_message`'s computed `reply`
   is never actually sent over WhatsApp for text messages — `whatsapp_endpoints.py`'s webhook
   handler calls `route_lead_message(lead_id, event["text"])` and discards the return value
   entirely. Only `route_lead_document` (Change I, the RUT/extractos flow) ever calls
   `send_whatsapp_message`. This means the sales_interest/payment_confirmation/unknown replies
   Taty "says" have never actually reached a real lead over WhatsApp, in any archived change to
   date — invisible until now because no real WhatsApp number/token exists to notice it with. This
   is a genuine, separate gap (call it "Taty's text replies aren't sent") — **not fixed here**,
   since doing so wasn't part of this change's proposed scope (per CLAUDE.md §7, a new gap found
   mid-change must become its own spec update, not a silent fix). Flagged for a follow-up change.
3. **Live smoke test, adapted to this reality**: since the webhook doesn't surface or send the
   reply text, verification focused on confirming the new integration path (real LLM + real KB
   call, in production, for the first time) executes correctly rather than inspecting reply
   content:
   - Fiscal-question case (`"que pasa si no declaro la renta a tiempo"`, disposable test lead):
     `200`, `4.796s`. Railway logs confirm: `_classify_fiscal_question`'s LLM call succeeded via
     Groq (after `openrouter_free` failed on a pre-existing, unrelated bad-model-ID config issue,
     not introduced by this change); `retrieve_similar` attempted a real OpenAI embeddings call,
     hit `429 Too Many Requests`, and **correctly fell back to the in-memory KB backend** rather
     than crashing (`KB[pgvector]: query embedding failed, falling back to memory` — confirms
     `kb_seeding_service.py`'s existing degradation path works under real rate-limiting); no
     traceback anywhere in the request.
   - Off-topic case (`"hola, buenos dias"`, second disposable test lead): `200`, `0.852s` — exactly
     one LLM call (classification only), zero KB/embedding calls, confirming `retrieve_similar` is
     correctly skipped when `is_fiscal_question=False`.
   - **Bonus real-server confirmation**: both requests' `get_tax_profile` calls hit a real `406 Not
     Acceptable` from PostgREST (the actual server response `.maybe_single()` is designed to
     handle for 0 rows, per `taty-persona-fields`' Stage 11 fix) and were correctly absorbed
     without crashing — confirms that earlier fix works against the real server, not just the
     mocked `postgrest-py` client behavior verified in unit tests.
   - Both disposable test leads (no tax profiles were created, since the `unknown` branch doesn't
     write persona fields) cleaned up.
4. No new flag — reuses `WHATSAPP_CANONICAL`.

## Accepted risks / limitations (carried from design.md)

- **Bounded to the `unknown`-intent fallback only** — `sales_interest`/`payment_confirmation`
  remain deterministic keyword classification, unchanged, per design.md Decision 1.
- **No conversational memory** — each message is still handled independently.
- **KB corpus freshness/coverage** is out of scope for this change.
- **LLM latency**: fiscal-question replies take ~5s (2 sequential LLM calls + KB retrieval) vs
  <1s for non-fiscal messages — acceptable for WhatsApp's async nature, not addressed further here.

## New gap flagged (not part of this change)

Taty's `route_lead_message` replies (across all three intents: sales_interest,
payment_confirmation, and now the KB-grounded unknown fallback) are computed but never sent over
WhatsApp — `whatsapp_endpoints.py` discards the return value. This should become its own OpenSpec
change (wire `send_whatsapp_message(phone, reply)` into the webhook handler after
`route_lead_message`), since per CLAUDE.md §7 a newly-found gap must be proposed as a spec update,
not patched informally inside this change.

## Verification evidence

- Railway deployment `756cd369`: `SUCCESS`, confirmed responding.
- Live webhook smoke test: both fiscal and off-topic cases return `200`, with Railway logs
  confirming the correct code path (KB search + 2 LLM calls vs 1 LLM call only) executed for each,
  and both a real embeddings-API failure and a real PostgREST 406 were handled gracefully.
- Full regression suite: 91/92 green (1 pre-existing, unrelated failure confirmed present on
  `main` before this change).
