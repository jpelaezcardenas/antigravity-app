## 1. Setup + verification

- [x] 1.1 Created branch `feature/taty-kb-and-react-router`.
- [x] 1.2 Re-confirmed `retrieve_similar`'s signature and the `"__global__"` client_id convention in
      `kb_seeding_service.py`, and `get_anonymized_ai_response`'s signature in `secure_llm.py` — no
      drift.

## 2. Fiscal-question classification — TDD

- [x] 2.1 Wrote failing tests for `_classify_fiscal_question(message) -> Dict[str, Any]`
      (returns `{"is_fiscal_question": bool, "search_query": str}`), mocking
      `get_anonymized_ai_response` directly. Confirmed failing (function didn't exist).
- [x] 2.2 Implemented `_classify_fiscal_question` in `taty_lead_router.py`, calling
      `get_anonymized_ai_response(..., response_format="json", required_keys={"is_fiscal_question",
      "search_query"})`.
- [x] 2.3 Green.

## 3. KB-grounded synthesis — TDD

- [x] 3.1 Wrote failing tests for `_synthesize_kb_reply(message, chunks) -> str`, mocking
      `get_anonymized_ai_response` directly (text mode).
- [x] 3.2 Implemented `_synthesize_kb_reply`.
- [x] 3.3 Green.

## 4. Wire into the `unknown` branch — TDD

- [x] 4.1 Wrote failing tests for the extended `unknown` branch of `route_lead_message`: fiscal
      question + chunks found → reply is the synthesized text; fiscal question + zero chunks found
      → graceful "no tengo esa información" reply, `_synthesize_kb_reply` NOT called; non-fiscal
      message → original static reply unchanged, no KB call, no synthesis call;
      `_classify_fiscal_question` raising → falls back to the original static reply. Confirmed
      failing.
- [x] 4.2 Implemented the wiring in `route_lead_message`'s `unknown` branch, wrapped in a
      try/except around the classification call per design.md Decision 5 (graceful degradation).
- [x] 4.3 41/41 green in `test_taty_lead_router.py`. **Caught a test-hygiene bug during this
      step**: two pre-existing tests (`test_persona_state_persisted_creates_missing_tax_profile`,
      `test_independiente_sets_es_asalariado_false`) send messages that fall into the `unknown`
      branch and didn't mock `_classify_fiscal_question` — they were silently making real LLM
      network calls (13s vs 1.5s baseline gave it away). Fixed by adding the mock to both,
      confirming zero real network calls in the unit suite (back to ~4s).

## 5. Verify + DB state (MANDATORY before Stage 11)

- [x] 5.1 Ran the full targeted suite: 91/92 green across
      `test_taty_lead_router.py`/`test_crm_service_b2c_logic.py`/`test_crm_b2c_endpoints.py`/
      `test_whatsapp_channel.py`/`test_whatsapp_endpoints.py`/`test_document_storage_service.py`/
      `test_kb_seeding.py`/`test_secure_llm.py`. The 1 failure
      (`test_pulso_analyze_endpoint_anonymizes_outbound_prompt`) is a pre-existing
      starlette/httpx `TestClient.__init__() got an unexpected keyword argument 'app'`
      environment incompatibility, confirmed present on `main` before this change too (via
      `git stash`) — not a regression.
- [x] 5.2 Wrote `openspec/changes/taty-kb-and-react-router/reports/2026-07-20-step5-verification.md`.

## 6. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 6.1 Committed (`98d4632`), fast-forward merged to `main`, pushed.
- [x] 6.2 Railway deploy `756cd369` reached `SUCCESS`. No new flag — reuses `WHATSAPP_CANONICAL`.
- [x] 6.3 **Live smoke test, adapted mid-flight**: discovered `route_lead_message`'s reply is never
      actually sent over WhatsApp by `whatsapp_endpoints.py` (return value discarded for text
      messages, pre-existing since Change D — flagged as a new, separate gap, not fixed here).
      Verification therefore focused on confirming the real integration path executes correctly:
      fiscal-question message → `200` in 4.8s, Railway logs confirm a real Groq LLM call succeeded
      for classification, `retrieve_similar` hit a real OpenAI embeddings `429` and correctly fell
      back to the in-memory KB backend (no crash); off-topic message → `200` in 0.85s, exactly one
      LLM call (classification only), zero KB/embedding calls, confirming the KB path is correctly
      skipped. Bonus: both requests' `get_tax_profile` calls hit a real PostgREST `406` and were
      correctly absorbed by the `.maybe_single()` fix from `taty-persona-fields`, confirming that
      fix works against the real server. Both disposable test leads cleaned up.
- [x] 6.4 Created deployment report at
      `openspec/changes/taty-kb-and-react-router/reports/2026-07-20-deployment.md`, including the
      newly-flagged "replies aren't sent" gap.

## 7. Archive

- [x] 7.1 Synced the ADDED `taty-whatsapp-sales-router` requirement into `openspec/specs/`
      (appended to the existing spec file), archived via `git mv` to
      `openspec/changes/archive/2026-07-20-taty-kb-and-react-router/`.
