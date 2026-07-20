# Step 5 verification — taty-kb-and-react-router

Date: 2026-07-20

## Test results

`test_taty_lead_router.py`: 41/41 green (7 new + 34 pre-existing, 2 pre-existing tests updated to
mock the new call site — see below).

Full targeted suite: 91/92 green. The 1 failure
(`test_secure_llm.py::test_pulso_analyze_endpoint_anonymizes_outbound_prompt`) is confirmed
pre-existing on `main` (reproduced via `git stash` before applying this change's diff) — a
`starlette.testclient.TestClient.__init__() got an unexpected keyword argument 'app'` version
incompatibility unrelated to this change, not a regression.

## Test-hygiene bug caught and fixed

Two pre-existing tests send messages that fall into `route_lead_message`'s `unknown` intent branch
("Sí, soy asalariado", "Soy independiente, trabajo por mi cuenta") without mocking the new
`_classify_fiscal_question` call site — they were silently making real, unmocked LLM provider
network calls during unit tests (giveaway: suite runtime jumped from ~1.5s to ~13s). Fixed by
adding `patch("services.taty_lead_router._classify_fiscal_question", return_value={...})` to both,
restoring deterministic, network-free unit tests (~4s).

## Scope of the change

`services/taty_lead_router.py`:
- `_classify_fiscal_question(message) -> Dict[str, Any]` (new): one anonymized JSON-mode LLM call.
- `_synthesize_kb_reply(message, chunks) -> str` (new): one anonymized text-mode LLM call, grounded
  strictly in retrieved chunks.
- `route_lead_message`'s `unknown` branch (modified): wired to the above plus
  `services.kb_seeding_service.retrieve_similar` (imported, unmodified), with a try/except around
  classification for graceful degradation on LLM failure.
- `sales_interest`/`payment_confirmation` branches: untouched, confirmed by the full pre-existing
  test suite for those branches still passing unmodified.

## No migration, no new endpoint

Pure logic addition/extension to one existing module.
