# Step 4 verification — copywriter-rag

Date: 2026-07-20

## Test results

Full targeted suite, 45/45 green, zero regression:

```
tests/test_copywriter_service.py ............. (13)
tests/test_content_evaluator.py
tests/test_sell_machine_service.py
tests/test_sell_machine_endpoints.py
tests/test_kb_seeding.py
```

## Scope of the change

`services/copywriter_service.py`:
- `_build_grounding_query(report=None) -> str` (new): derives a KB retrieval query, favoring a
  telemetry report's `hook_performance` pain_tags when present.
- `_format_kb_grounding(chunks) -> str` (new): renders retrieved chunks as a prompt section,
  mirroring `_format_telemetry_report`'s style.
- `_llm_generate_hooks` (modified): now calls `retrieve_similar` against the shared `"__global__"`
  KB pool before building the prompt, wrapped in try/except so retrieval failure/emptiness never
  blocks hook generation.
- `generate_hooks`/`rewrite_hook` (unmodified): all 7 pre-existing tests, which mock
  `_llm_generate_hooks` at the call-point level, pass unmodified — confirming this change is fully
  additive at the internal level with zero externally-visible behavior change when KB content is
  unavailable.

## No migration, no new endpoint

Pure logic addition to one existing function.
