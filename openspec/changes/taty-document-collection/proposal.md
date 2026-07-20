## Why

Closes gap #2 from the plan-vs-build audit against the original Antigravity SOTA Sell Machine
design: "Taty ella misma recolecta el RUT y extractos... tu única intervención es hacer clic en
Transferir a Contadora". Today `LISTOS_CONTADORA` is reached the instant a human approves a
payment (`CrmService.approve_payment`) — no document collection happens at all, so the human
accountant receives an empty folder. This change makes Taty proactively request and store the two
required documents after payment approval, so `LISTOS_CONTADORA` genuinely means "ready for the
accountant," not just "paid."

## What Changes

- `channels/whatsapp.py`'s `normalize_whatsapp_webhook` is extended (additively) to also normalize
  WhatsApp document/image messages into the common event shape (`media_id`, `mime_type`), since
  today it silently drops any message without `text.body` — confirmed by reading the code, this
  is a real, previously-invisible gap, not a design choice.
- A new WhatsApp media downloader (2-step Graph API flow: fetch the temporary download URL from
  `media_id`, then download the bytes), following the exact "no credentials → return
  False/log, never call out empty" pattern already established by `send_whatsapp_message`.
- A new private Supabase Storage bucket (`crm-tax-documents`) for RUT/extractos files, admin-only
  access, signed URLs for the human accountant — the first file-storage pattern in this repo.
- Sequential document collection in `taty_lead_router.py`: once a payment is approved
  (`LISTOS_CONTADORA`), Taty proactively asks for the RUT first; once received, asks for
  extractos. Reuses the existing `crm_tax_profiles.rut_status`/`extractos_status` text columns as
  the collection state machine (`pending` → `requested` → `collected`) — no new status columns.
- A new `crm_tax_profiles` column to hold each document's storage path (needed since the existing
  columns are status-only, no path field exists — confirmed by reading Change B's schema).
- The proactive RUT request is triggered synchronously inside `CrmService.approve_payment`'s
  single call site, not a new background job (this repo deliberately has no scheduler/cron).

## Capabilities

### New Capabilities
- `taty-document-collection`: WhatsApp media ingestion, private document storage, and the
  sequential RUT→extractos collection flow gating the accountant handoff.

### Modified Capabilities
- `taty-whatsapp-sales-router`: `normalize_whatsapp_webhook` gains document/image support
  (additive — existing text-message scenarios are unaffected); a new document-arrival routing path
  is added alongside the existing text-message routing.

## Impact

- **New migration**: `crm-tax-documents` Storage bucket (via Supabase MCP, inserting into
  `storage.buckets`/policies on `storage.objects` — this repo's first non-table-DDL migration) +
  a new `crm_tax_profiles` column for the document storage path.
- **Modified**: `channels/whatsapp.py` (additive normalizer extension, new downloader function),
  `services/taty_lead_router.py` (new document-routing function), `services/crm_service.py`
  (`approve_payment` gains the proactive-RUT-request trigger, called synchronously).
- **No new Railway flag** — reuses `WHATSAPP_CANONICAL`.
- **No frontend change in this change** — the ready-for-accountant state becomes queryable but a
  dedicated "Transferir a Contadora" Búnker button is deferred (not requested yet, and the human
  can already see `LISTOS_CONTADORA` + both statuses `collected` in the existing Kanban).
- **Explicitly out of scope**: any change to `POR_APROBAR`'s HITL "Aprobar Pago" gate — document
  collection strictly happens AFTER that gate, never before or in place of it.
