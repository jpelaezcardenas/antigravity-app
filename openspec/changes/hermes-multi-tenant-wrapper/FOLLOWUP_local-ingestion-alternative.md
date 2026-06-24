# Follow-up: Local Daily Upload as SyncManager Alternative

**Date noted:** 2026-06-24
**Status:** Idea captured, not yet scoped

## Context

Phase 2 (SyncManager API integration) and Phase 3 (WSL hardening for the SyncManager tunnel) are
deferred — the commercial negotiation with SyncManager has not been closed (see `tasks.md`
Ground Truth Correction).

Juan David's direction (2026-06-24): instead of waiting on SyncManager, explore ingesting
Contexia's own accounting data (Contexia as "cliente cero") through **daily local/manual upload
by the admin**, independent of any third-party API.

## Not yet defined (needs its own scoping before becoming tasks)

- What gets uploaded daily — DIAN XML export, Siigo CSV/Excel export, something else?
- Upload mechanism — PWA file upload form? Direct Supabase Storage? CLI script run locally by
  the admin?
- Where it lands — feeds into the existing Shadow GL tables (`erp_journal_entries`,
  `erp_journal_lines`, `dian_xml_documents` — confirmed live in `kpynymwghfwshvcvevxq` from
  Phase 4) or a new staging table?
- Validation — same Agent Critic / arithmetic checks Phase 4 already built for Shadow GL, or
  something simpler given manual upload is lower-volume?
- Frequency/SLA — literally daily, or just "whenever the admin has time"?

## Why this is a separate change, not folded into this one

`hermes-multi-tenant-wrapper`'s actual remaining scope (per the Ground Truth Correction) is
fixing the tenant_id/RLS bugs in Phase 1 — unrelated to how data gets ingested. The local-upload
idea is a new ingestion path that should get its own `proposal.md`/`design.md` once the above
questions are answered, likely as a small addition to the existing Shadow GL work
(`agentic-performance-management-phase4`, already archived) rather than a sub-task of the
multi-tenant wrapper.
