## Context

Re-confirmed by reading the live source:
- `channels/whatsapp.py`'s `normalize_whatsapp_webhook` extracts only `message.text.body`; any
  message without it (WhatsApp Cloud API sends document messages as `{"type": "document",
  "document": {"id": ..., "mime_type": ..., "filename": ...}}`, image messages similarly under
  `"image"`) is silently skipped — a genuine, previously-invisible gap, not an intentional
  exclusion.
- `crm_tax_profiles` columns (confirmed live earlier this session):
  `id, tenant_id, lead_id, es_asalariado, topes, rut_status, extractos_status, obligado_declarar,
  notes, created_at, updated_at`. `rut_status`/`extractos_status` are plain `text` columns with no
  existing values written anywhere — a clean slate to define as a state machine.
- `CrmService.approve_payment(lead_id, approved_by)` (`crm_service.py:245`) is called from exactly
  one place: `presentation/crm_endpoints.py`'s single `POST /leads/{lead_id}/approve-payment`
  route. It transitions `POR_APROBAR → LISTOS_CONTADORA` and stamps the Wompi transaction
  `APPROVED`. This is the correct, single hook point for triggering document collection — no new
  endpoint or background job needed.
- No existing migration in this repo creates a Supabase Storage bucket — every prior migration is
  plain table DDL. Supabase Storage buckets are managed via `storage.buckets`/policies on
  `storage.objects` (a Postgres-backed API, reachable the same way as any other table via
  `apply_migration`/`execute_sql`).
- `WHATSAPP_TOKEN` is unset in production (no real WhatsApp Business number exists yet, per Change
  D's accepted limitation) — this change's live media-download path is therefore untestable
  end-to-end with a real inbound file until that credential exists; only the storage
  bucket/RLS/signed-URL mechanics can be verified for real in Stage 11.

## Goals / Non-Goals

**Goals:**
- Make document (image/PDF) WhatsApp messages visible to the system at all (currently invisible).
- Store RUT/extractos privately, with signed, time-limited access for the human accountant.
- Drive a simple, unambiguous sequential collection flow (RUT first, then extractos) triggered
  automatically the moment a payment is approved — no keyword classification needed.
- Never let document collection happen before or bypass the existing `POR_APROBAR` HITL gate.

**Non-Goals:**
- A dedicated "Transferir a Contadora" Búnker button — not requested; the existing Kanban already
  shows `LISTOS_CONTADORA` + both statuses, which is sufficient visibility for now.
- Real end-to-end verification with an actual WhatsApp-delivered file — impossible without a real
  WhatsApp Business number (same accepted limitation as Change D).
- OCR/validation of document contents (e.g. confirming a RUT PDF is actually a RUT) — Taty trusts
  that whatever arrives after her explicit request is the document she asked for, matching the
  sequential-collection design decision (no content classification).
- Retry/reminder logic if a lead never responds with a document — deferred, same posture as
  Change H's "no TTL for abandoned transactions" decision.

## Decisions

**1. `rut_status`/`extractos_status` become a 3-value state machine: `pending → requested →
collected` — reusing the existing columns, no new status columns.**
`pending` (default, before payment approval): nothing has happened yet. `requested`: Taty has
asked for this specific document and is waiting. `collected`: the document arrived and was stored.
**Correction found during Stage 8 DB verification**: the live `crm_tax_profiles` table already had
CHECK constraints on these two columns restricting values to `('pending', 'collected')` only — not
visible from `information_schema.columns` alone, only discovered when a test insert failed. One
existing seeded row already used `collected` as its terminal value. The migration was updated to
`ALTER` both constraints, adding `'requested'` to the allowed set and keeping `'collected'` as the
terminal state (not inventing `'received'`, which was this design's original word choice before the
constraint was discovered) — reusing exactly the pre-existing vocabulary. This fits cleanly into
the existing `text` columns with no other schema change — only a new column is needed for the
storage *path* (see Decision 2), since no existing column can hold that.

**2. New `crm_tax_profiles` columns: `rut_storage_path`, `extractos_storage_path` (text,
nullable).**
Store the Supabase Storage object path (not a URL — URLs are generated on demand via signed URL,
never persisted, since they expire) once each document is uploaded. This is the one genuinely new
piece of schema this change needs.

**3. New private Storage bucket `crm-tax-documents`, admin-only RLS, signed URLs on demand.**
Mirrors this repo's established admin-only table RLS pattern, translated to Storage: a policy on
`storage.objects` restricting `SELECT`/`INSERT` to admin users of the owning tenant (same `role =
'admin'` check pattern as every table migration this session). Files are named
`{lead_id}/{rut|extractos}.{ext}` for a stable, predictable path. The accountant never gets a raw
public URL — only a short-lived signed URL generated when needed (e.g. via a future Búnker view,
out of scope for this change's UI).

**4. Sequential collection state lives in `crm_tax_profiles`, not a new conversation-state table.**
`route_lead_document`'s logic: read `rut_status`; if `pending`/`requested` and no RUT stored yet,
this incoming document IS the RUT — store it, set `rut_status='collected'`, then immediately ask
for extractos (`extractos_status` set to `requested`, message sent via `send_whatsapp_message`).
If `rut_status='collected'` already, this document must be the extractos — store it, set
`extractos_status='collected'`. No column tracks "which one are we currently asking for" separately
— it's derived from `rut_status`/`extractos_status`'s current values, keeping the state machine
minimal.

**5. The proactive RUT request is triggered synchronously inside `CrmService.approve_payment`,
right after the stage transition succeeds — not a new background job.**
This repo deliberately has no scheduler (confirmed across three prior changes' design docs). The
single existing call site (`POST /leads/{lead_id}/approve-payment`) is already synchronous and
already the exact moment a human confirms the payment — the natural, only correct trigger point.
`approve_payment` sets `rut_status='requested'` and calls `send_whatsapp_message` (existing,
unmodified) with the RUT request text.

**6. `normalize_whatsapp_webhook`'s extension is purely additive.**
The existing text-extraction branch is untouched; a new branch checks for `message.get("type") in
("document", "image")` and, if present, builds an event with `media_id`/`mime_type` populated and
`text` empty — the caller (the webhook handler) is updated to route based on which fields are
present, not by changing the existing text-message code path at all.

**7. Document collection is strictly downstream of `POR_APROBAR`'s HITL gate.**
`route_lead_document` (the new document-handling function) only proceeds if the lead's current
`crm_leads.stage` is `LISTOS_CONTADORA` (i.e., a human has already approved the payment) — a
document arriving before that stage is acknowledged but not processed as RUT/extractos (Taty
replies that there's nothing pending yet), preventing any possibility of Taty acting on
document-collection logic for an unapproved payment.

## Risks / Trade-offs

- **[Risk] Cannot verify a real file upload end-to-end without a real WhatsApp number.** →
  Mitigation: same accepted limitation as Change D; unit tests cover the full logic against
  fabricated media payloads, and the Storage bucket/RLS/signed-URL mechanics ARE verified for real
  in Stage 11 (uploading a test file directly, generating a signed URL, confirming admin-only
  access).
- **[Risk] A malformed/wrong-type file (e.g. a random photo, not the RUT) gets accepted as the
  RUT since there's no content validation.** → Mitigation: explicitly a Non-Goal — accepted
  trade-off of the sequential-collection design; a human accountant reviewing `LISTOS_CONTADORA`
  folders would catch a wrong file, same as any human review step.
- **[Risk] No retry/reminder if a lead never sends the requested document.** → Mitigation:
  deferred, consistent with this session's existing precedent (no TTL/staleness handling built
  yet for Wompi transactions either).

## Migration Plan

1. Migration: `crm-tax-documents` Storage bucket + RLS policies + the two new
   `crm_tax_profiles` columns (`rut_storage_path`, `extractos_storage_path`), applied via Supabase
   MCP, re-applied to confirm idempotency.
2. `channels/whatsapp.py`: additive normalizer extension + media downloader, TDD.
3. New Storage upload/signed-URL helper functions, TDD (mocked Supabase Storage client).
4. `taty_lead_router.py`: `route_lead_document`, TDD.
5. `crm_service.py`: `approve_payment` gains the proactive RUT-request trigger, TDD (confirm
   existing `approve_payment` tests still pass — this is an additive change to that function).
6. Stage 11: commit, merge, verify Railway green (no new flag). Live-verify the Storage bucket for
   real (upload a test file, generate a signed URL, confirm admin-only RLS blocks a non-admin
   read) via Supabase MCP. Logic-only verification of the WhatsApp document flow (fabricated
   payloads), same limitation as Change D — documented explicitly, not glossed over. Deployment
   report, archive.
- **Rollback**: revert the code changes; the Storage bucket and new columns are additive and
  unused by any other code path — safe to leave in place or drop if truly needed.

## Open Questions

- Should a dedicated "Transferir a Contadora" Búnker button be built later, once both documents
  are `collected`? Deferred — not requested, and the existing Kanban view already surfaces this
  state.
