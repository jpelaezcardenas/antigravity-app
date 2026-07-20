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
- [x] 3.3 **Second bug found live during Stage 11 smoke testing, fixed within this same change**:
      `parsed.get("parsing_error")` crashed with `AttributeError: 'list' object has no attribute
      'get'` whenever the LLM legitimately returns a top-level JSON array (exactly what
      Copywriter's system prompt requests: "una lista de objetos") — present in both
      `_get_json_with_retry` and `_get_json_with_retry_custom_order` (identical line, both fixed
      for consistency, per design.md's own goal of byte-identical behavior between the two
      variants). Fixed via an `isinstance(parsed, dict)` guard; added 2 regression tests
      (`TestJsonRetryListShapedResponse`). 57/57 green after this second fix, zero regression.

## 4. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 4.1 Committed (`1ae83fb`, `ddb30bd`), merged to `main`, pushed.
- [x] 4.2 Railway deploys `ed1279cc` then `85e1246d` reached `SUCCESS`. No flag involved (internal
      utility, always active).
- [x] 4.3 **Live smoke test — two rounds**: first round (fix #1 only) returned `200` but still the
      deterministic fallback, revealing a second bug (`AttributeError` on list-shaped responses,
      fixed within this same change — see report). Second round (both fixes deployed):
      `POST /sell-machine/hooks/generate` → `200`, returned hooks completely different from the
      known deterministic fallback set — definitive proof the real LLM JSON path works
      end-to-end. Railway logs confirm zero `TypeError`/`AttributeError`, and the existing
      retry-with-re-prompt logic correctly recovered from one malformed-JSON attempt.
- [x] 4.4 Created deployment report at
      `openspec/changes/fix-llm-engine-required-keys/reports/2026-07-20-deployment.md`, documenting
      both bugs.

## 5. Archive

- [x] 5.1 No delta specs to sync (internal bugfix, no capability document changed). Archived via
      `git mv` to `openspec/changes/archive/2026-07-20-fix-llm-engine-required-keys/`.
