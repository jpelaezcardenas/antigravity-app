# Review — task taty_doc_collection_task2

**Verdict:** APPROVED

## Scope check (tasks.md / design.md)

Task 2 requires: extend `route_lead_document()` to accept a `data_url`-sourced download,
branching instead of always calling `download_whatsapp_media`, keeping the Graph `media_id`
path untouched and covered by its existing tests. TDD.

- `apps/backend/services/taty_lead_router.py`: `route_lead_document()` signature changed to
  `(lead_id, media_id: Optional[str] = None, mime_type: str = "application/octet-stream", *,
  data_url: Optional[str] = None)`. `media_id`/`mime_type` remain the same positional slots,
  so the four pre-existing positional call sites are untouched. New branch:
  `if data_url: download_chatwoot_attachment(data_url) else: download_whatsapp_media(media_id)`
  — matches design.md's integration-point spec verbatim ("either `media_id` ... or `data_url`").
  Only the import line and this one function were touched in this file.
- `apps/backend/tests/test_taty_lead_router.py`: two new tests added inside
  `TestRouteLeadDocument` (`test_data_url_source_calls_download_chatwoot_attachment_not_graph_media`,
  `test_data_url_download_failure_does_not_update_any_status`). No existing test in this file was
  modified — confirmed by diff.
- No changes to `apps/backend/api/*` (Task 3's endpoint), `apps/chatwoot-bridge/*` (Task 4), or
  any migration file — confirmed via `git status --short apps/backend/api apps/chatwoot-bridge
  apps/backend/migrations`, which shows only the unrelated, pre-existing untracked
  `0052_crm_leads_source.sql` from a different change (`b2c-social-lead-capture`, per the
  session's git status snapshot), not touched by this task.
- `channels/whatsapp.py` and `test_whatsapp_channel.py` diffs present in the working tree are
  Task 1's work (already reviewed/approved separately — `progress/review_taty_doc_collection_task1.md`
  exists), not introduced by Task 2.

## Independent verification

- Re-ran `py -3.11 -m pytest tests/test_taty_lead_router.py tests/test_whatsapp_channel.py -q`
  from `apps/backend` myself: **88 passed, 3 warnings in 72.99s** — matches the report's pasted
  output exactly.
- Independently confirmed the "60 pre-existing + 2 new = 62" claim via
  `pytest tests/test_taty_lead_router.py -q --collect-only` → **62 tests collected**. Consistent
  with the report's math (88 = 62 + 26 from `test_whatsapp_channel.py`).
- Read the new tests: they patch `download_chatwoot_attachment`/`download_whatsapp_media` at the
  `services.taty_lead_router` import site (correct patch target given the `from channels.whatsapp
  import (download_chatwoot_attachment, download_whatsapp_media, ...)` import), assert the right
  one is called and the other is *not* called, and assert on `result["processed"]` and
  `upload_tax_document`/`update_tax_profile` call args — real behavioral assertions, not just
  "no exception."

## Code quality / conventions

- Fully typed (`Optional[str]`, explicit return type `Dict[str, Any]` unchanged).
- Docstring extended in English, references design.md's finding and the two mutually-exclusive
  sources — consistent with documentation standards.
- `data_url` made keyword-only, a reasonable, narrowly-scoped design choice to avoid ambiguity
  with the existing 3-positional-arg call shape; matches design.md's framing.
- No type-checking disabled, no stubs/mocks of the function under test (the two new tests mock
  the *download* dependency, not `route_lead_document` itself — respects the `real-data-ingestion-
  mvp` lesson about not mocking the boundary under test, Decision #22).

## Conclusion

Task 2 is scoped correctly, TDD was followed (red confirmed before the code change per the
report, independently re-verified green after), the Graph `media_id` path is provably untouched
(explicit `assert_not_called()` in the new test), and no unrelated files (Task 3/4/5 endpoint,
bridge, migrations) were touched. All numeric claims in the report were independently reproduced.
