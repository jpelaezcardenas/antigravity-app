## 1. Setup + verification

- [x] 1.1 Created branch `feature/taty-document-collection`.
- [x] 1.2 Re-confirmed `crm_tax_profiles` columns, `CrmService.approve_payment`'s single call
      site, and `normalize_whatsapp_webhook`'s current text-only extraction — no drift.
- [x] 1.3 Confirmed WhatsApp Cloud API's document/image message shape via web search:
      `message["document"] = {filename, mime_type, sha256, id}`,
      `message["image"] = {mime_type, sha256, id}` (no `filename`).

## 2. Migration — Storage bucket + new columns

- [x] 2.1 Wrote `test_tax_documents_schema.py` (gated by `RUN_TAX_DOCUMENTS=1`, mirrors
      `test_operator_tasks_schema.py`'s pattern) asserting the two new columns and the private
      bucket exist.
- [x] 2.2 Authored `apps/backend/migrations/0026_crm_tax_documents.sql`: `rut_storage_path`/
      `extractos_storage_path` columns on `crm_tax_profiles`; `crm-tax-documents` private bucket;
      admin-only RLS policy on `storage.objects` scoped to that bucket (single-tenant
      simplification documented in the migration comment — `storage.objects` has no `tenant_id` to
      join against). **Amended after discovering a live CHECK constraint** during 8.2 DB
      verification: `rut_status`/`extractos_status` were already restricted to
      `('pending','collected')` only (invisible from `information_schema.columns`), with one
      existing seeded row using `collected`. Extended both constraints to add `'requested'`,
      reusing `collected` as the terminal value instead of the design's original `'received'`
      word choice.
- [x] 2.3 Applied via Supabase MCP `apply_migration`; re-applied via `execute_sql` — idempotent,
      no errors.
- [x] 2.4 Verified live via direct SQL: both columns exist; bucket exists with `public=false`.

## 3. WhatsApp normalizer extension — TDD

- [x] 3.1 Wrote tests: a fabricated document-message payload normalizes with `media_id`/
      `mime_type` populated and empty `text`; an image-message payload normalizes the same way.
      Confirmed failing (new fields didn't exist yet).
- [x] 3.2 Extended `normalize_whatsapp_webhook` additively (new `message_type`/`media` detection
      alongside the existing text extraction, both feeding the same event dict).
- [x] 3.3 8/8 tests green (2 new + 6 pre-existing), zero regression.

## 4. WhatsApp media downloader — TDD

- [x] 4.1 Wrote tests: `download_whatsapp_media(media_id)` returns `None` and logs when
      `WHATSAPP_TOKEN` unset; when configured, calls the 2-step Graph API flow (mocked
      `httpx.AsyncClient`, 2 sequential `GET` calls) and returns `{"content": bytes, "mime_type":
      str}`; returns `None` if the metadata fetch fails. Confirmed failing (function didn't
      exist).
- [x] 4.2 Authored `download_whatsapp_media` in `channels/whatsapp.py`.
- [x] 4.3 11/11 tests green (3 new + 8 pre-existing), zero regression.

## 5. Storage upload + signed URL helpers — TDD

- [x] 5.1 Wrote tests for `upload_tax_document(lead_id, document_type, file_bytes, mime_type) ->
      str` (returns the storage path) and `get_signed_document_url(storage_path) -> str`, mocking
      the Supabase Storage client directly. Confirmed failing (module didn't exist).
- [x] 5.2 Authored `services/document_storage_service.py` (new module — cleaner than colocating in
      `taty_lead_router.py` since this is generic document storage, reusable beyond the WhatsApp
      flow).
- [x] 5.3 3/3 tests green.

## 6. Sequential document routing — TDD

- [x] 6.1 Wrote tests for `route_lead_document(lead_id, media_id, mime_type)`: `rut_status`
      `requested` → downloads, uploads, sets `rut_status='collected'` + `rut_storage_path`,
      requests extractos (`extractos_status='requested'`, sends a WhatsApp message to the lead's
      real phone via `_get_lead_phone`); `rut_status='collected'` and `extractos_status` not yet
      `collected` → downloads, uploads, sets `extractos_status='collected'` +
      `extractos_storage_path`; lead's `crm_leads.stage` is not `LISTOS_CONTADORA` → no processing;
      download failure → no status change. Confirmed failing (function didn't exist).
- [x] 6.2 Authored `route_lead_document` in `taty_lead_router.py`. Caught and fixed a bug during
      TDD: initially called `send_whatsapp_message(lead_id, ...)` instead of the lead's actual
      phone number — added `_get_lead_phone(lead_id)` (mirrors `_get_lead_stage`'s pattern) to fix
      this before it reached tests.
- [x] 6.3 Wired the WhatsApp webhook handler (`presentation/whatsapp_endpoints.py`) to call
      `route_lead_document` when a normalized event has `media_id` set, `route_lead_message`
      otherwise.
- [x] 6.4 28/28 tests green (4 new `route_lead_document` + 24 pre-existing), zero regression.

## 7. `approve_payment` proactive RUT trigger — TDD

- [x] 7.1 Wrote a test: `CrmService.approve_payment` now also creates a `crm_tax_profiles` row if
      missing, sets `rut_status='requested'`, and calls `send_whatsapp_message` with the lead's
      real `whatsapp_phone`. Confirmed failing (new behavior didn't exist). **Note**: this
      required making `approve_payment` `async` (to `await send_whatsapp_message`) — updated its
      one call site (`crm_endpoints.py`'s `approve-payment` route, now `async def` + `await`) and
      the existing Change B tests (converted to `@pytest.mark.asyncio` + `AsyncMock`).
- [x] 7.2 Extended `approve_payment` in `crm_service.py`.
- [x] 7.3 111/111 tests green across the full targeted suite (this change + Changes B/D/E/F/G/H
      test files), zero regression.

## 8. Verify + DB state (MANDATORY before Stage 11)

- [x] 8.1 Ran the full targeted suite: 111/111 green (30 new/rewritten + 81 pre-existing, zero
      regression). Confirmed no `contexia-app/` files touched.
- [x] 8.2 **Critical finding**: discovered a live CHECK constraint restricting `rut_status`/
      `extractos_status` to `('pending','collected')` only — amended the migration to add
      `'requested'` and reuse `'collected'` (not the design's original `'received'` word choice,
      corrected throughout code/tests/OpenSpec artifacts). Confirmed live via Supabase MCP: a
      disposable lead + tax-profile simulation lands correctly with the corrected vocabulary.
      **Storage bucket verified via real HTTP calls** to the Storage REST API (not just SQL
      introspection): uploaded a real test file, generated a signed URL that correctly returns the
      content, confirmed the public/unauthenticated path reports the bucket as not found (private,
      as designed). All test artifacts cleaned up.
- [x] 8.3 Wrote `openspec/changes/taty-document-collection/reports/2026-07-20-step8-verification.md`.

## 9. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 9.1 Commit backend changes in scoped commits referencing this change id.
- [ ] 9.2 Merge to `main` (check for conflicts) and push.
- [ ] 9.3 Confirm Railway backend deploy completes green. No new flag — reuses
      `WHATSAPP_CANONICAL` (already live).
- [ ] 9.4 Live smoke test (logic-only for the WhatsApp document flow, since no real WhatsApp
      number exists yet — same accepted limitation as Change D): approve a real test lead's
      payment via the live endpoint, confirm `rut_status` becomes `requested` and a
      `send_whatsapp_message` call was attempted (will no-op/log since `WHATSAPP_TOKEN` is unset —
      confirm this fails gracefully, not with an error); POST a fabricated document-message
      webhook payload for that lead and confirm the document flow logic runs correctly end-to-end
      against the real database (status transitions, storage path recorded) even though the
      actual file bytes can't be really downloaded from Meta without a real token — decide exactly
      how to simulate this gap explicitly in the smoke test and document it plainly in the
      deployment report.
- [ ] 9.5 **Separately, verify the Storage bucket for real** (this part doesn't depend on a real
      WhatsApp number): upload a real test file via the service-role client, generate a signed
      URL, confirm it's reachable, confirm a non-admin/anon request is blocked, delete the test
      file.
- [ ] 9.6 Create deployment report at
      `openspec/changes/taty-document-collection/reports/YYYY-MM-DD-deployment.md`, explicitly
      documenting the WhatsApp-number limitation (same as Change D) and the real Storage
      verification performed.

## 10. Archive

- [ ] 10.1 Sync the new `taty-document-collection` capability AND the modified
      `taty-whatsapp-sales-router` requirement into `openspec/specs/` (merge the MODIFIED
      requirement into the existing spec file, same process as Change H) using `git mv` for the
      archive move, and archive this change once Stage 11 is confirmed complete and verified live.
