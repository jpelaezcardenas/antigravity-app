## 1. Setup + verification

- [x] 1.1 Created branch `feature/fix-llm-engine-required-keys`.
- [x] 1.2 Re-confirmed `_parse_llm_response`'s real signature, `_validate_required`'s signature,
      and `_get_json_with_retry`'s reference implementation — no drift.

## 2. Fix `_get_json_with_retry_custom_order` — TDD

- [x] 2.1 Wrote failing tests in `test_llm_engine.py`'s new `TestJsonRetryCustomOrder` class:
      valid JSON on first attempt; retries on missing required key; returns last attempt with
      `parsing_error` after retries exhausted. Confirmed failing — reproduced the exact live
      `TypeError: _parse_llm_response() takes from 2 to 4 positional arguments but 5 were given`.
- [x] 2.2 Rewrote `_get_json_with_retry_custom_order` to mirror `_get_json_with_retry`'s pattern
      exactly: parse via `_parse_llm_response(raw_response, synonyms=synonyms,
      list_keys=list_keys)`, then `_validate_required(parsed, required_keys)`, matching
      retry-prompt phrasing.
- [x] 2.3 18/18 green in `test_llm_engine.py` (3 new + 15 pre-existing, 1 e2e-gated skip),
      zero regression.

## 3. Verify + DB state (MANDATORY before Stage 11)

- [x] 3.1 Ran the full targeted suite: 55/55 green (1 pre-existing skip) across
      `test_llm_engine.py`/`test_copywriter_service.py`/`test_content_evaluator.py`/
      `test_sell_machine_service.py`/`test_sell_machine_endpoints.py`, zero regression.
- [x] 3.2 Wrote `openspec/changes/fix-llm-engine-required-keys/reports/2026-07-20-step3-verification.md`.

## 4. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 4.1 Commit + merge to `main` (check for divergence) + push.
- [ ] 4.2 Confirm Railway deploy green. No flag involved (internal utility, always active).
- [ ] 4.3 Live smoke test: call the real `POST /api/v1/sell-machine/hooks/generate` endpoint;
      confirm `200`, and inspect Railway logs to confirm NO `TypeError:
      _parse_llm_response() takes ...` occurs, and that the response reflects fresh LLM-generated
      hook content (not the deterministic fallback set that appeared in every prior Stage 11 this
      session) — the definitive proof this bug is fixed.
- [ ] 4.4 Create deployment report at
      `openspec/changes/fix-llm-engine-required-keys/reports/YYYY-MM-DD-deployment.md`.

## 5. Archive

- [ ] 5.1 No delta specs to sync (internal bugfix, no capability document changed). Archive via
      `git mv` once Stage 11 is confirmed complete.
