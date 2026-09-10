# Review — task taty_doc_collection_task3

**Verdict:** APPROVED

## Scope

Task 3 of `taty-document-collection-wiring`: new `POST /internal/whatsapp/document`
endpoint, INTERNAL_API_KEY fail-closed, same module family as
Siigo/Gmail/voice-note `/internal/*` endpoints, TDD.

## Duplicate-report check

Confirmed via `ls progress/` — exactly one implementer report exists for this task
(`progress/impl_taty_doc_collection_task3.md`). No `_v2`, no conflicting second report.
The implementer's own report documents that a prior, un-reported session had already
left the deliverable files untracked in the working tree; this session verified that
prior work against the contract and took explicit ownership of it rather than
rewriting blind or silently trusting it. No governance concern here — flagging
resolved, not open.

## Contract check vs design.md / proposal.md

- `apps/backend/presentation/whatsapp_document_endpoints.py` — new file, `router =
  APIRouter()`, route `POST /whatsapp/document` (mounted under `/internal` prefix in
  `main.py`, giving the full `/internal/whatsapp/document` path per spec).
- Body: `WhatsappDocumentRequest(lead_id: str, data_url: str, mime_type: str =
  "application/octet-stream")`. design.md's prose says `file_type` but Task 2's
  already-approved `route_lead_document` signature (verified directly,
  `services/taty_lead_router.py:517-523`) takes `mime_type`, not `file_type` — the
  implementer's naming is correct against the real callee, design.md's prose is
  simply imprecise there. Not a deviation worth rejecting; contract intent (forward
  the MIME/content-type string) is preserved.
- Forwards to `route_lead_document(lead_id, mime_type=..., data_url=...)` — confirmed
  by reading both the endpoint source (line 76-80) and the real function signature.
  `media_id` is never passed (left `None`), matching the "Chatwoot payload never
  carries a Graph media_id" finding in proposal.md/design.md.
- Returns `{"processed": bool}` verbatim as a 200, never raised for a `False` result —
  matches proposal.md's "processed: False is a normal outcome" stance.

## ARCHITECTURE.md Decision #22 / #26 fail-closed + fail-loud pattern

- `_verify_internal_key`: unset env → 503 checked first; wrong/missing header → 401.
  Identical structure and env var name (`INTERNAL_API_KEY`) to
  `presentation/voice_endpoints.py::_verify_internal_key` (byte-for-byte same logic,
  confirmed by direct read of both files).
- `apps/backend/main.py:255-274`: the whole `/internal/*` router-registration block
  (siigo_sync, ingest_file, voice, cadence, voice_outbound, and now
  whatsapp_document) is **unconditional** — no `try/except` around the imports or
  `include_router` calls. Line 255-259 has an explicit comment citing this exact
  history: a prior try/except swallowed a `NameError` and silently dropped both
  `/internal/*` routes while the app reported itself healthy (Decision #22). The new
  router is added inside that same unconditional block, at line 265 (import) and 273
  (`include_router`) — verified directly, not just from the diff description in the
  implementer's report.

## Sibling pattern (voice_endpoints.py) comparison

Read both files side by side. Auth check order is identical: key verified before any
body/payload handling in both. The new endpoint appropriately omits voice_endpoints'
extra concerns (feature-flag gate, base64 decode, size cap, safety-gate re-check,
lead/phone lookup, Graph media upload+send) because Task 3's job is strictly
"authenticate + forward to the one function that owns download/gating" — consistent
with proposal.md's stated non-goal of not re-implementing that logic here.

## Test verification (live re-run, not trusted from the report)

Ran directly:
```
cd apps/backend && py -3.11 -m pytest tests/test_whatsapp_document_endpoint.py -v
```
Result: **7 passed**, 3 warnings (pre-existing deprecation warnings, unrelated),
79.37s. Matches the report's pasted output (report claimed 101.40s — a live re-run
now taking 79s is a machine timing difference, not a discrepancy in outcome).

Read the full test file. Assertions are real, not just "no exception":
- 4 auth tests assert exact status codes (503/503/401/401) via `excinfo.value.status_code`.
- `test_delegates_to_route_lead_document_with_data_url` monkeypatches
  `route_lead_document` and asserts the exact tuple of args forwarded
  (`("lead-42", None, "image/jpeg", "https://x/y.pdf")`) — proves argument mapping,
  not just "didn't crash".
- `test_not_processed_result_is_returned_not_raised` asserts `result.processed is
  False` is returned normally, not raised.
- `test_uses_the_real_route_lead_document_not_a_reimplementation` asserts
  `endpoints.route_lead_document is services.taty_lead_router.route_lead_document`
  by identity — this is the boundary-mocking guard called out in Decision #22 (a test
  must not mock the exact function it claims proves real wiring); here it is present
  and does the opposite (proves the real function is imported, unmocked, at module
  scope).

No test mocks the endpoint's own auth-check function or forges around the boundary
being tested.

## metrics_endpoints.py import failure — not in scope, correctly not touched

The implementer noted `py -3.11 -c "import main"` fails on a pre-existing,
unrelated `AttributeError` in `presentation/metrics_endpoints.py` (line 33, FastAPI/
pydantic version mismatch). Confirmed this is irrelevant to Task 3: the test file
imports `presentation.whatsapp_document_endpoints` directly, never `main`, so the
7/7 pass is unaffected. This matches the documented 25F/28E pre-existing baseline
(MEMORY.md) and is out of scope for this change (no task touches
`metrics_endpoints.py`). Not a blocker.

## Checkpoints

- C1 Respects ARCHITECTURE.md (Decision #22 fail-closed/fail-loud, /internal/*
  boundary, no scope creep into media_id/Graph path or Wompi gate): [x]
- C2 Respects backend-standards.md (typed pydantic models, async, no bare
  exceptions swallowed): [x]
- C3 TDD — test file exists, asserts real outcomes (status codes, exact forwarded
  args, return values, function identity), not just absence of exception: [x]
- C4 No fabricated stubs / no disabled type-checking / no hand-edited `app/`: [x]
  (backend-only change, `app/` untouched)
- C5 Tests actually green, verified by reviewer's own live run, not just trusted
  from the implementer's pasted output: [x]
- C6 main.py registration unconditional, no try/except swallowing: [x]
- C7 Only one implementer report for this task, no unresolved duplication: [x]
- C8 Docs-sync: no new container/external dependency introduced (endpoint reuses
  the existing `/internal/*` family and `INTERNAL_API_KEY` pattern already
  documented under Decision #22/#26) — ARCHITECTURE.md update not required for
  this task: [x]

## Required changes

None. Task 3 is reviewer-approved as implemented.
