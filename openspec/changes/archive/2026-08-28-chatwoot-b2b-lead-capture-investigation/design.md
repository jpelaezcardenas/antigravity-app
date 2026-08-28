## Context

The freemium-onboarding master plan's routing tree says: a natural person crossing the UVT
threshold with continuous financial operations → Campaña 2 (SaaS B2B) lead; a simpler natural
person → Campaña 1 (Renta Natural, B2C) client, transactional, never touching the PWA. Subdomain 2
(`auditoria-sombra-lead-capture-investigation`) verified the GTM wizard's lead-capture path for
Campaña 2. This investigation asks the symmetric question about Contexia's other live, active
conversational channel: WhatsApp via Chatwoot, staffed by Taty. Chatwoot is not hypothetical
infrastructure — confirmed running locally (4 Docker containers: `chatwoot-web`, `-worker`,
`-postgres`, `-redis`, up 6+ hours, `chatwoot-web` bound to `localhost:3020`), and is the
production channel for Renta Natural today (ARCHITECTURE.md's Chatwoot + bridge container entry).

Method: a 5-agent research workflow (full trace of `taty_lead_router.py`, the fiscal-profile
detection logic, `crm_leads`' schema and any graduation path, the Chatwoot custom-attribute
auto-tagging pipeline, and the Chatwoot→HubSpot sync scope), followed by a synthesis pass. The two
highest-stakes claims — `classify_lead_intent`'s exact 3-outcome set and the auto-tagging
pipeline's exact field mappings — were independently re-verified by directly reading
`apps/backend/services/taty_lead_router.py:78-106` and `apps/chatwoot-bridge/main.py:55-120` in
full before writing this document; both match the workflow's evidence verbatim.

## Goals / Non-Goals

**Goals:**
- Determine definitively whether a Campaña-2-eligible WhatsApp prospect is surfaced, flagged, or
  captured as a B2B lead anywhere in the current codebase.
- If a partial mechanism exists (e.g. a schema field that's defined but unused), document exactly
  how far it goes and what's missing to complete it.
- Inform Subdomain 4's design honestly about which channels feed the B2B alta funnel today.

**Non-Goals:**
- No code changes. This is a read-only investigation; any fix belongs to a future change.
- Not designing the WhatsApp-to-B2B-lead bridge itself — only establishing whether one exists.
- Not re-litigating the Chatwoot custom-attribute schema design (`chatwoot-mcp-and-attributes`) —
  only confirming what it does and doesn't currently drive.

## Decisions

**Finding — no bridge exists. A Campaña-2-eligible WhatsApp prospect vanishes into Campaña 1.**

Tracing every layer of the pipeline confirms this, independently and consistently across all five
research angles:

- **Taty's intent classifier has no B2B category.** `classify_lead_intent()`
  (`apps/backend/services/taty_lead_router.py:91-106`, read in full) returns exactly one of
  `"sales_interest"`, `"payment_confirmation"`, or `"unknown"` — a closed, B2C-tax-filing-scoped
  set. There is no `"b2b_interest"` or equivalent outcome, and no code path anywhere checks message
  content for company/SAS/persona-jurídica signals as an intent.

- **The nearest "business continuity" signal is a red herring for this purpose.**
  `_detect_persona_fields()` (`taty_lead_router.py:247-273`) extracts `es_asalariado`, `topes`, and
  `obligado_declarar` — the last computed by comparing an extracted peso amount against
  `UMBRAL_RENTA_COP`, the Renta Natural filing threshold, not a UVT-crossing/persona-jurídica
  check. Its own docstring calls it "a preliminary internal signal, not a legally authoritative
  determination." Even where it fires, `obligado_declarar=True` drives no branch: stage advancement
  (`taty_lead_router.py:350-373`) is keyed purely off keyword-based sales intent, entirely
  independent of `persona_fields`.

- **`crm_leads` has no schema surface for this at all.** Migration `0022` (creation) +
  `0040` (HubSpot sync columns) give the full column list: `id, tenant_id, full_name,
  whatsapp_phone, email, stage, source, last_message, score, assigned_agent, created_at,
  updated_at, hubspot_contact_id, hubspot_deal_id, last_synced_at`. No qualification-tier or
  business-type column exists. An exhaustive grep across `apps/backend/` for
  graduation/promotion/conversion patterns (`graduat`, `upgrade.*b2b`, `b2b_client`, `to_tenant`,
  `convert.*lead`, `promote.*lead`) returned zero matches. `crm_service.py::approve_payment()`
  (`:474-523`) — the terminal lifecycle function when a lead reaches HITL approval — never creates
  or references a `tenants`/`b2b_clients` row.

- **The Chatwoot attribute schema has the *shape* of a B2B signal, but it's structurally
  unreachable.** The 16-attribute schema (`chatwoot-mcp-and-attributes`, archived 2026-08-15,
  `design.md:32-38`) defines `tipo_contribuyente` with dropdown values including `SAS` and
  `no_responsable_IVA`, and `servicio_interes` including `creacion_empresa`/`CFO` — genuinely
  B2B-shaped options. But that same design doc explicitly scoped the auto-tagging pipeline itself
  out as a fast-follow (`design.md:11-12`: "Not building the Hermes auto-tagging pipeline ... —
  tracked as a fast-follow"). The pipeline that *does* exist,
  `_auto_tag_chatwoot()` (`apps/chatwoot-bridge/main.py:84-117`, confirmed by direct reading), maps
  only the two real intents (`sales_interest`→`ventas`, `payment_confirmation`→`cobranza`) and one
  boolean (`es_asalariado`→`persona_natural`/`regimen_simple`, a binary collapse where `SAS` is
  never reachable). The schema's B2B-shaped dropdown values are writable only by a human agent
  manually tagging a conversation in the Chatwoot UI — no automated writer ever selects them.

- **HubSpot sync cannot express a routing difference even if the tag existed.**
  `apps/hermes-hubspot-poller/poller.py:61-69` hardcodes every `crm_leads` Deal to
  `settings.HUBSPOT_DEAL_PIPELINE` (default `"default"`, `config.py:24`) — a single free-tier
  pipeline, not derived from any per-record field. `stage_mapping.py:11-29`'s dealstage map falls
  back to the `NUEVOS` mapping for any unrecognized stage, structurally incapable of escaping the
  Renta Natural funnel. `b2b_clients` sync is a fully separate call site (`upsert_company`,
  `_sync_b2b_client`) that never creates a Deal — the two object types have no shared code path.

**Additional confirming evidence (found by the reviewer, not the original research pass):**
`apps/chatwoot-bridge/main.py:177` hardcodes `{"tipo_lead": "b2c_whatsapp", "estado": "nuevo"}` on
every new WhatsApp contact's Chatwoot attributes — every lead that reaches this channel is
unconditionally stamped as B2C at intake time, an even more direct piece of evidence than the
absence-based findings above.

**Net:** the only existing mechanism by which a Campaña-2-eligible WhatsApp prospect could be
surfaced today is a human Contexia operator manually reading the conversation in the Chatwoot
inbox and manually acting on it — nothing systematic exists. This is a real, previously
undocumented gap in the freemium-onboarding master plan, parallel in shape to the Auditoria Sombra
finding in Subdomain 2, but opposite in direction: Subdomain 2 found persistence that already
existed where the plan assumed a gap; this investigation finds a gap where the plan implicitly
assumed (by never checking) that WhatsApp/Chatwoot was either out of scope or already covered.

## Risks / Trade-offs

- [Risk] Subdomain 4 (`crm-alta-tiered-provisioning`) could be designed assuming the only inputs
  to the B2B alta funnel are the founder's manual contacts and the GTM wizard, missing a real
  (if currently manual) source: WhatsApp conversations a human operator already reads daily. →
  Mitigation: flagged explicitly below as an open question for that subdomain's design.
- [Risk] Building the missing bridge (a B2B-intent classifier + auto-tagging + a routing decision)
  is nontrivial new scope, not a quick fix — the fiscal-profile detection, the Chatwoot tagging
  pipeline, and the HubSpot sync would all need coordinated changes to carry a "this is Campaña 2"
  signal end-to-end. → Mitigation: this investigation deliberately does not scope that work; it
  only establishes that the gap is real, sized roughly (three separate subsystems), and worth a
  founder decision on priority.
- [Risk] The schema's existing B2B dropdown values (`SAS`, `creacion_empresa`, `CFO`) could create
  a false sense that "Chatwoot already tracks this" during a future design review, since they
  visibly exist in Chatwoot's own attribute config. → Mitigation: documented explicitly here that
  they are schema-only, never automatically populated.

## Migration Plan

Not applicable — this change makes no code or infrastructure changes. Nothing to deploy, nothing
to roll back. Stage 11 does not apply, for the same reason established in
`auditoria-sombra-lead-capture-investigation`'s design.md.

## Open Questions

- [ENGINEERING/FOUNDER] Decide whether closing this gap is in scope for the freemium-onboarding
  master plan at all, or a separate, later GTM initiative — it's a new B2B-intent detection +
  tagging + routing capability, not a small fix, and the master plan's current subdomains (3-6)
  don't depend on it existing.
- [ENGINEERING] If pursued: does the fix belong in `taty_lead_router.py`'s classifier (add a
  B2B-intent category), in the Chatwoot auto-tagging pipeline (complete the fast-follow that
  `chatwoot-mcp-and-attributes` deliberately deferred), in both, or in a new standalone
  classification step? This investigation deliberately does not decide — it establishes the
  current-state gap only.
- [ENGINEERING] Confirm with the founder/spec author whether ARCHITECTURE.md Decision #19's
  "detección de perfil fiscal" phrase was ever intended to include persona-jurídica/UVT-crossing
  detection, or whether it always meant only `_detect_persona_fields()`'s Renta-Natural-scoped
  fields — this affects whether the gap found here is a regression from original intent or simply
  scope that was never built.
- [FOUNDER ACTION] In the interim (no automated bridge), consider whether Contexia's Chatwoot
  operators should be given an explicit, lightweight prompt/checklist to manually tag a
  conversation as B2B-shaped (`tipo_contribuyente: SAS`, etc.) when they spot one — the dropdown
  values already exist and are usable today, just never auto-populated.
