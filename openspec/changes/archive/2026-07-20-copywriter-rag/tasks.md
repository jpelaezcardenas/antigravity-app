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

- [x] 5.1 Committed (`9932cf7`), fast-forward merged to `main`, pushed.
- [x] 5.2 Railway deploy `ab41edfd` reached `SUCCESS`. No new flag — reuses
      `SELL_MACHINE_CANONICAL`.
- [x] 5.3 **Live smoke test**: `POST /sell-machine/hooks/generate` → `200`, correct hook shape.
      Railway logs confirm this change's `retrieve_similar` call executed for real and gracefully
      degraded under a real OpenAI embeddings `429`. A **separate, pre-existing bug** in
      `agents/llm_engine.py` (`_get_json_with_retry_custom_order` calls `_parse_llm_response` with
      an unsupported `required_keys` arg) then caused the real LLM call to fail post-success,
      correctly triggering `generate_hooks`'s own deterministic fallback — satisfying the
      requirement's contract exactly, but meaning fresh LLM-grounded content wasn't observed this
      run. Flagged as a new gap, not fixed (unrelated file, out of this change's scope).
- [x] 5.4 Created deployment report at
      `openspec/changes/copywriter-rag/reports/2026-07-20-deployment.md`, including the flagged
      `llm_engine.py` bug.

## 6. Archive

- [x] 6.1 Synced the MODIFIED `sell-machine-creative-swarm` delta into `openspec/specs/` (merged
      into the existing spec file), archived via `git mv` to
      `openspec/changes/archive/2026-07-20-copywriter-rag/`.
