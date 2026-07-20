## 1. Setup + verification

- [x] 1.1 Created branch `feature/copywriter-rag`.
- [x] 1.2 Re-confirmed `retrieve_similar`'s signature/`"__global__"` convention and
      `_llm_generate_hooks`'s/`_format_telemetry_report`'s current bodies — no drift.

## 2. Grounding-query derivation — TDD

- [x] 2.1 Wrote failing tests for `_build_grounding_query(report=None) -> str`: generic DIAN-pains
      query when `report` is None; derives a query mentioning the report's `hook_performance`
      pain_tags when present. Confirmed failing.
- [x] 2.2 Implemented `_build_grounding_query`.
- [x] 2.3 Green.

## 3. Wire retrieval into hook generation — TDD

- [x] 3.1 Wrote failing tests for the extended `_llm_generate_hooks`: retrieved chunks appear in
      the LLM prompt; empty retrieval doesn't block generation; retrieval raising doesn't block
      generation. Confirmed failing.
- [x] 3.2 Implemented the wiring in `_llm_generate_hooks` (new `_format_kb_grounding` helper),
      wrapped in a try/except around the retrieval call.
- [x] 3.3 13/13 green in `test_copywriter_service.py` (6 new + 7 pre-existing, all pre-existing
      tests mock `_llm_generate_hooks` at the call-point level and were unaffected by the internal
      change), zero regression.

## 4. Verify + DB state (MANDATORY before Stage 11)

- [x] 4.1 Ran the full targeted suite: 45/45 green across
      `test_copywriter_service.py`/`test_content_evaluator.py`/`test_sell_machine_service.py`/
      `test_sell_machine_endpoints.py`/`test_kb_seeding.py`, zero regression.
- [x] 4.2 Wrote `openspec/changes/copywriter-rag/reports/2026-07-20-step4-verification.md`.

## 5. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 5.1 Commit + merge to `main` (check for divergence) + push.
- [ ] 5.2 Confirm Railway deploy green. No new flag — reuses `SELL_MACHINE_CANONICAL`.
- [ ] 5.3 Live smoke test: call the real `POST /api/v1/sell-machine/hooks/generate` endpoint;
      confirm `200`, correct hook shape, and inspect Railway logs for a real `retrieve_similar`
      call (or its graceful degradation) having occurred during the request.
- [ ] 5.4 Create deployment report at
      `openspec/changes/copywriter-rag/reports/YYYY-MM-DD-deployment.md`.

## 6. Archive

- [ ] 6.1 Sync the MODIFIED `sell-machine-creative-swarm` delta into `openspec/specs/` (merge into
      the existing spec file), archive via `git mv` once Stage 11 is confirmed complete.
