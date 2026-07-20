## Why

`crm_tax_profiles` already has `topes` (jsonb) and `obligado_declarar` (boolean) columns, live in
production, but no code path ever detects or writes to either. Taty currently only persists
`es_asalariado` (via `_detect_persona_fields` in `taty_lead_router.py`) — despite that same
function's docstring already claiming to extract `topes`. This is the last unclosed sliver of gap
#8 from the plan-vs-build audit: Taty is supposed to build a persona profile of the lead across the
conversation, but two of its four fields are permanently empty. Closing this now, before the larger
ReAct/KB rework (gaps #3/#4), keeps the existing deterministic keyword-classification router the
single place persona detection lives, rather than splitting that logic across two paradigms.

## What Changes

- Extend `_detect_persona_fields(message)` in `taty_lead_router.py` to also detect UVT-relevant
  qualifying signals from the message text (consignaciones/ingresos/compras/patrimonio mentions with
  a peso amount) and accumulate them into a `topes` dict on the lead's tax profile, merging with
  whatever partial `topes` already exist rather than overwriting.
- Once enough `topes` fields are known to make a determination against the existing
  `UMBRAL_RENTA_UVT` / `UMBRAL_RENTA_COP` constants (`core/constants.py` — already computed, not
  reinvented), set `obligado_declarar` (true/false) on the same profile.
- No new columns, no migration — both target columns already exist live.

## Capabilities

### New Capabilities
(none — this extends existing WhatsApp sales-router behavior, not a new capability)

### Modified Capabilities
- `taty-whatsapp-sales-router`: the "Detected persona state is persisted to the lead's tax
  profile" requirement is being extended to also cover `topes` and `obligado_declarar`, not just
  `es_asalariado`.

## Impact

- `apps/backend/services/taty_lead_router.py` (`_detect_persona_fields`, `route_lead_message`) —
  only files touched.
- `crm_tax_profiles.topes` / `.obligado_declarar` — first code paths ever writing to these live
  columns.
- No frontend, no migration, no new endpoint.
