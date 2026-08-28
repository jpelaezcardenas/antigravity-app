# Review — task chatwoot-b2b-lead-capture-investigation

**Verdict:** APPROVED

## Verification method

Independently re-read every file cited in `design.md`'s Decisions section (not the investigation's
own summary): `apps/backend/services/taty_lead_router.py` (full, 542 lines),
`apps/chatwoot-bridge/main.py` (full, 217 lines), `apps/backend/services/crm_service.py`
(`approve_payment` + grep for `tenants`/`b2b_client`), `apps/backend/migrations/0022_...sql` and
`0040_...sql` (plus a repo-wide grep confirming no other migration alters `crm_leads`),
`apps/hermes-hubspot-poller/{poller.py,config.py}`, and
`openspec/changes/archive/2026-08-15-chatwoot-mcp-and-attributes/design.md`. Also ran an
independent grep across `apps/backend/` for `campana|campaign_2|b2b_lead|graduar|es_juridica|
persona_juridica|uvt` not limited to the investigation's own search terms.

## Checkpoint-by-checkpoint verification

1. **`taty_lead_router.py`** — CONFIRMED exactly. `classify_lead_intent()` (lines 91–106) returns
   only `"payment_confirmation"`, `"sales_interest"`, `"unknown"` (lines 102/104/106) — closed set,
   no B2B branch. `_detect_persona_fields()` (lines 247–273) sets only `es_asalariado`, `topes`,
   `obligado_declarar`; `obligado_declarar` (line 271) compares `renta_amount >= UMBRAL_RENTA_COP`
   (imported from `core.constants`, line 27) — a Renta Natural filing threshold, not a UVT-crossing
   or persona-jurídica test. Stage advancement (lines 356–373, design.md said 350–373 — off by 6
   lines, immaterial) branches purely on `intent`/`current_stage`; `persona_fields` is written to
   `crm_tax_profiles` (line 354) but never read back to gate a stage transition.

2. **Migrations** — CONFIRMED. Grepped every migration file for `ALTER TABLE crm_leads` /
   `ADD COLUMN`: only `0022` (creation) and `0040` (adds `hubspot_contact_id`, `hubspot_deal_id`,
   `last_synced_at`) touch this table. Full column set has no business-type/tier column.

3. **`crm_service.py::approve_payment()`** (lines 474–528, design.md said 474–523 — close enough)
   — CONFIRMED. Touches only `crm_leads`, `crm_wompi_transactions`, `crm_tax_profiles`, and sends a
   WhatsApp message. No reference to `tenants`/`b2b_clients` inside the function. (Those tables
   *are* used elsewhere in the file — `create_b2b_client`, `list_b2b_clients`, etc. — but that is a
   fully separate code path never called from the WhatsApp lead-approval flow, exactly as claimed.)

4. **`apps/chatwoot-bridge/main.py::_auto_tag_chatwoot`** (lines 84–117) — CONFIRMED. Maps exactly
   2 intents (`sales_interest`→`ventas`, `payment_confirmation`→`cobranza`, lines 63–66) plus one
   boolean (`es_asalariado`→`persona_natural`/`regimen_simple`, lines 108–111, a binary collapse
   where `SAS`/jurídica values are structurally unreachable). Worth noting for the record (not a
   correctness defect in the investigation): lines 174–178 also hardcode
   `{"tipo_lead": "b2c_whatsapp", "estado": "nuevo"}` for every brand-new contact — an even more
   explicit "this channel is B2C-only" signal than what design.md quoted. This *strengthens* the
   investigation's finding; it is not a missed bridge.

5. **Archived `chatwoot-mcp-and-attributes/design.md`** — CONFIRMED. Decision 5 lists
   `tipo_contribuyente` with `SAS` as a dropdown option and `servicio_interes` with
   `creacion_empresa`/`CFO`. The Non-Goals section explicitly scopes the auto-tagging pipeline out
   as a "fast-follow" (line 12).

6. **HubSpot poller** — CONFIRMED. `config.py:24` hardcodes `HUBSPOT_DEAL_PIPELINE: str = "default"`;
   `poller.py:63` uses it unconditionally for every `crm_leads` Deal. `_sync_b2b_client` (line 95)
   calls `hubspot_client.upsert_company` (line 105) and explicitly never creates a Deal (comment,
   line 110) — a fully separate call site from `sync_leads`/deal creation.

7. **Exhaustive independent grep** — ran my own grep (not reusing the investigation's search list)
   for `campana|campaign_2|b2b_lead|graduar|es_juridica|persona_juridica|uvt` across
   `apps/backend/`. All UVT hits are fiscal-constant/Centinela-rule usages unrelated to B2B lead
   routing (`core/constants.py`, `centinela_service.py`'s Régimen Simple threshold check,
   Taty's fiscal KB answers) — no missed graduation/detection path found. `campana` hits are all in
   `social_ops_service.py` (an unrelated internal content-ops capability), not lead routing.

## OpenSpec artifact sanity check

- `proposal.md`'s "no capability changes" / empty specs is justified: this change genuinely makes
  zero code changes, confirmed by the `Impact` section listing only files *read*.
- Omission of a Stage 11 section in `tasks.md` (documented in `design.md`'s Migration Plan) is
  consistent with CLAUDE.md §8, which mandates Stage 11 for changes that reach production —
  there is nothing to deploy here. Same precedent as the sibling investigation
  `auditoria-sombra-lead-capture-investigation`, correctly cited.

## Checkpoints
- C1 (claims match real code): [x]
- C2 (no fabricated stubs / no hand-edited `app/` / no disabled type-checking): [x] — N/A, no code
  touched.
- C3 (TDD / tests for new functionality): [x] — N/A, investigation-only, no new functionality.
- C4 (docs-sync: architecture container/dependency change reflected in ARCHITECTURE.md): [x] — N/A,
  no container or dependency changed by this investigation.
- C5 (Stage 11 / deployment): [x] — correctly and explicitly not applicable; documented as such.

## Required changes (if any)
None. Two immaterial line-number drifts (stage-advancement block cited as 350–373, actually
356–373; `approve_payment` cited as 474–523, actually 474–528) do not misrepresent the code's
behavior and are not worth blocking on.

## Note for Subdomain 4 design (non-blocking observation)
The bridge's `{"tipo_lead": "b2c_whatsapp"}` hardcode (`apps/chatwoot-bridge/main.py:177`) is an
even stronger piece of evidence for the "no bridge exists" finding than what design.md cited —
worth folding into Subdomain 4's context if that design references this investigation.
