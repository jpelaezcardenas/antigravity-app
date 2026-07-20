# Deployment report — taty-document-collection

Date: 2026-07-20

## Summary

Change deployed and verified live in production. Approving a payment now proactively triggers
Taty's document-collection flow (RUT then extractos); a real, production bug found live during
this Stage 11 was fixed before the loop could be confirmed working.

## Commits deployed

- `94487fa` — feat(taty): add RUT/extractos document collection (Change I)
- `c3929e9` — fix(crm): crm_tax_profiles inserts were missing tenant_id (NOT NULL)

## Stage 11 steps executed

1. **9.1-9.2** — Committed on `feature/taty-document-collection`, fast-forward merged to `main`
   (confirmed no divergence via `git merge-base`), pushed.
2. **9.3 — Railway deploy + a real bug found and fixed live.** The first deploy of commit
   `94487fa` reached `SUCCESS` and the app came up. Calling the real
   `POST /api/v1/crm/leads/{lead_id}/approve-payment` endpoint against a real test lead returned a
   **500 Internal Server Error**. Railway logs showed the real traceback:
   `postgrest.exceptions.APIError: null value in column "tenant_id" of relation
   "crm_tax_profiles" violates not-null constraint`. Root cause: `CrmService.approve_payment`'s
   new `crm_tax_profiles` insert (Change I) never included `tenant_id`. Investigating further
   found the **exact same bug pre-existing since Change D** in `taty_lead_router.py`'s
   `_create_empty_tax_profile` — never caught because its unit tests always mock that function
   entirely rather than exercising its real body against the live constraint. Fixed both
   (commit `c3929e9`), added a regression test for each, re-ran the full suite (38/38 green),
   merged, pushed, and re-deployed. **This deploy also needed 2 manual `railway_redeploy`
   triggers** across the two commits — same recurring Railway platform slow-boot pattern seen
   throughout this session (no crash signature in any of the intermediate cold-start gaps).
3. **9.4 — Live smoke test** (post-fix), exercised for real against production:
   1. Created a real test lead at `POR_APROBAR` with an `APPROVED` Wompi transaction via Supabase
      SQL.
   2. `POST /api/v1/crm/leads/{lead_id}/approve-payment` → **`200`** (previously `500` before the
      fix). Confirmed via Supabase SQL: `crm_tax_profiles` row created with the correct
      `tenant_id`, `rut_status="requested"`.
   3. `POST /api/v1/channels/whatsapp/webhook` with a fabricated document-message payload for that
      lead → `{"ok":true,"events_processed":1}`, no crash. Confirmed via Supabase SQL:
      `rut_status` correctly stayed `"requested"` (not falsely advanced to `"collected"`) and
      `rut_storage_path` stayed `null` — the real media download failed gracefully (`WHATSAPP_TOKEN`
      unset in production, no real WhatsApp Business number exists yet, same accepted limitation
      documented in Change D), and `route_lead_document` correctly did nothing further rather than
      recording false progress.
   4. All test artifacts (lead, tax profile, Wompi transaction) cleaned up afterward.
4. **9.5 — Storage bucket verified for real** during Section 8 (pre-deploy), not re-verified again
   here since it doesn't depend on the deploy — see `reports/2026-07-20-step8-verification.md` for
   the real upload/signed-URL/blocked-public-access round trip.
5. **9.6 — This report.**

## Accepted risks / limitations (carried from design.md)

- **No real WhatsApp Business number exists** — the actual file-download step of the document flow
  is unverifiable end-to-end until one is provisioned. Confirmed today that it fails gracefully
  (no crash, no false status progress) rather than silently corrupting state.
- **No content validation (OCR)** — Taty trusts whatever arrives after her explicit request is the
  document she asked for.
- **No retry/reminder** if a lead never responds with a document.
- **No dedicated "Transferir a Contadora" Búnker button** — the existing Kanban already surfaces
  `LISTOS_CONTADORA` + both statuses.

## A note on the bug found

This is the first time in this session that a live Stage 11 smoke test surfaced a genuine
production bug (as opposed to Railway platform slow-boot noise) — the discipline of always
exercising the real endpoint against real data before declaring a change complete, rather than
trusting unit tests alone, is what caught it. The same bug had existed silently in
`taty_lead_router.py` since Change D (archived) without being noticed, because Change D's Stage 11
smoke test never happened to exercise the "create a missing tax profile" branch against the real
database in a way that triggered the constraint.

## Verification evidence

- Railway deployment (final: commit `c3929e9`): `SUCCESS`, confirmed responding.
- Live `POST /crm/leads/{lead_id}/approve-payment`: `200` (fixed from `500`), correct
  `tenant_id`/`rut_status` in Supabase.
- Live `POST /channels/whatsapp/webhook` (document message): `200`, no crash, correctly no false
  status progress when the media download fails.
- Storage bucket: verified for real in Section 8 (upload + signed URL + blocked public access).
