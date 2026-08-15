# Deployment Report — fix-whatsapp-phone-normalization-dedup

**Date:** 2026-08-15
**Commit:** `ab75327`
**Railway deployment:** `2526c8b7-f51c-477a-9b33-7b276a99f5d3` — `SUCCESS`

## What shipped

- `_normalize_whatsapp_phone` (`crm_service.py`) fixed to always strip the `+`, so both phone formats collapse to one canonical value.
- `wizard_service.run_renta_diagnostico` routed through `CrmService.whatsapp_intake` instead of its own broken direct insert (wrong columns, invalid hardcoded tenant_id — never once succeeded live).
- One-time data cleanup: merged the two duplicate `crm_leads` rows found during the HubSpot/Chatwoot sync verification — re-pointed the orphaned `crm_tax_profiles` row, deleted the duplicate lead and its HubSpot Contact+Deal.
- Bonus fix: `hermes-hubspot-poller`'s scheduled task now launches via `silent_runner.vbs` (same pattern as its sibling pollers), eliminating a visible console-window flash on every 5-min tick.

## Live verification

- 15/15 new tests passing (`test_crm_whatsapp_intake.py`, `test_wizard_renta_diagnostico_lead_capture.py`).
- Full backend suite: 816 passed, 39 pre-existing failures confirmed unrelated (httpx/starlette version mismatch, dead legacy shadow-GL test modules) — none touch the files changed here.
- `crm_leads`: 5 → 4 real rows, confirmed via `SELECT count(*)`.
- Next poller tick (post-cleanup): `leads_synced: 4, b2b_clients_synced: 10`, zero failures.
- Railway redeploy: `SUCCESS`.

## Known follow-ups

- The founder's still-in-progress `chatwoot-mcp-and-attributes` OpenSpec change (separate thread) was left untouched throughout this session — worth a coordination check once that lands, in case it also touches `crm_leads` intake.
