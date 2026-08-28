## 1. Trace Taty's WhatsApp lead-intent classification

- [x] 1.1 Read `taty_lead_router.py` in full (`apps/backend/services/taty_lead_router.py:1-542`)
      and document every function, every table it reads/writes, and every occurrence of
      `tenant_id`/`b2b`/`b2b_clients`.
- [x] 1.2 Confirm `classify_lead_intent()`'s exact outcome set (`sales_interest` /
      `payment_confirmation` / `unknown`) and that no B2B/company-type category exists.
- [x] 1.3 Confirm `_detect_persona_fields()`'s exact fields (`es_asalariado`, `topes`,
      `obligado_declarar`) and that `obligado_declarar` is a Renta Natural filing-threshold
      check, not a UVT-crossing/persona-jurídica classifier, and drives no branch/flag/write.

## 2. Confirm no `crm_leads` → `tenants`/`b2b_clients` graduation path exists

- [x] 2.1 Read every migration touching `crm_leads` (0022 creation, 0040 alteration) and list
      the full current column set — confirmed no qualification-tier/business-type column.
- [x] 2.2 Exhaustive grep across `apps/backend/` for graduation/promotion/conversion patterns —
      zero matches.
- [x] 2.3 Read `crm_service.py::approve_payment()` (the terminal lead lifecycle function) in
      full — confirmed it never creates or references `tenants`/`b2b_clients`.

## 3. Trace the Chatwoot custom-attribute auto-tagging pipeline

- [x] 3.1 Read the 16-attribute schema definition
      (`openspec/changes/archive/2026-08-15-chatwoot-mcp-and-attributes/design.md`) — confirmed
      B2B-shaped dropdown values exist (`tipo_contribuyente: SAS`, `servicio_interes:
      creacion_empresa/CFO`), and that the auto-tagging pipeline was explicitly scoped out as a
      fast-follow in that same change.
- [x] 3.2 Read `_auto_tag_chatwoot()` (`apps/chatwoot-bridge/main.py:84-117`) in full — confirmed
      it maps only the 2 real intents + 1 boolean, and that `SAS`/jurídica values are
      structurally unreachable by this code path (a binary collapse to
      `persona_natural`/`regimen_simple`).

## 4. Trace the Chatwoot → HubSpot sync scope

- [x] 4.1 Read `apps/hermes-hubspot-poller/poller.py`, `config.py`, `stage_mapping.py` — confirmed
      every `crm_leads` row syncs to one hardcoded, env-driven Deal pipeline (`"default"`), with
      no per-record routing possible, and that `b2b_clients` sync (`upsert_company`) is a fully
      separate call site that never creates a Deal.

## 5. Independent spot-check (trust but verify)

- [x] 5.1 Re-read `apps/backend/services/taty_lead_router.py:78-106` directly (not via subagent
      summary) and confirmed `classify_lead_intent()`'s 3-outcome set matches verbatim.
- [x] 5.2 Re-read `apps/chatwoot-bridge/main.py:55-120` directly and confirmed the exact
      intent/field mappings match verbatim, including the `SAS`-unreachable binary collapse.

## 6. Write the deliverable

- [x] 6.1 Wrote the full findings, evidence, and design decisions into `design.md`.
- [x] 6.2 Wrote a founder/engineering-readable findings note to
      `reports/2026-08-28-findings.md`, distinct from `design.md`.
- [x] 6.3 Confirmed no code, spec, or living-doc changes are needed as part of *this* change —
      open items are recorded as follow-up questions in `design.md`, not silently fixed here.

Note: no Stage 11 (Deploy to Production) section — this change makes no code or infrastructure
change; see `design.md`'s Migration Plan.
