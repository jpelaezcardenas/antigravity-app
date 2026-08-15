## Context

Chatwoot exposes a full REST API (confirmed live all night: conversations, messages, contacts, labels, private notes/replies all work over `curl` with the account-scoped `api_access_token` header already stored in `apps/chatwoot-bridge/.env`). There is no dedicated Chatwoot MCP in the public registry (confirmed via `search_mcp_registry`, empty result). Contexia already has an established local-MCP pattern for exactly this situation: `contexia-mcp-servers/railway/` — official `mcp` Python SDK (`FastMCP`), one `<vendor>_<action>` tool per operation, credentials from a local `.env` (never committed), registered in the workspace-level `Projects/.mcp.json`.

## Goals / Non-Goals

**Goals:**
- Give any agent working this repo (Claude Code now, Hermes later) a reusable, typed tool surface over Chatwoot — no more hand-typed `curl`.
- Provision the founder's specified custom-attribute schema (contact + conversation level) so it exists in Chatwoot's UI and API before any automation tries to write to it.

**Non-Goals:**
- Not building the Hermes auto-tagging pipeline that would populate `intencion`/`resumen_ia`/etc. — that consumes this MCP's tools once built, but is separate, larger scope (LLM classification design, trigger point in the bridge's `process_incoming_message`, cost/latency tradeoffs). Tracked as a fast-follow.
- Not evaluating Chatwoot's native HubSpot integration app — separate question from "can an agent read/write Chatwoot."
- Not granting the MCP server (or Taty Bot's token) Administrator rights — see Decision #2.

## Decisions

**1. New sibling repo directory (`contexia-mcp-servers/chatwoot/`), not inside `antigravity-app`.**
Matches `railway/`'s placement exactly, for the same reason: this is agent tooling infrastructure, not product code the PWA/backend ships. Runs local (same machine as Hermes/the bridge/Docker), never on Railway/Vercel — same data-sovereignty principle as `ARCHITECTURE.md` decisions #1/#10. The Chatwoot API token stays on this machine, never in a cloud env var.

**2. Custom Attribute Definitions require an Administrator-role token — Taty Bot's agent token cannot create them.**
Found live: `POST /custom_attribute_definitions` with the bridge's existing `CHATWOOT_API_TOKEN` (owner: `taty-bot@contexia.online`, `role: "agent"`) returns `403 "You are not authorized to do this action"`. Confirmed via `GET /api/v1/profile` on that same token. This is expected Chatwoot RBAC, not a bug — attribute *definitions* (the schema) are an account-level setting; attribute *values* on a specific contact/conversation are not.
**Resolution for this change**: the MCP still ships a `chatwoot_create_custom_attribute_definition` tool (so it's ready to use), but it needs the founder's own Administrator-role token (or a fresh Personal Access Token from his own agent profile at `jpelaezcardenas@gmail.com`) supplied via a separate env var (`CHATWOOT_ADMIN_TOKEN`, optional — falls back to a clear error naming the missing var rather than silently using the agent token and failing with a confusing 403). **Provisioning the actual schema (task 3.x) is therefore a founder action**, not something this session can complete end-to-end — documented as such in tasks.md rather than silently skipped.
Deliberately NOT elevating Taty Bot to Administrator: that account is what the live production bridge authenticates as for every real customer conversation; broadening its scope beyond "operate conversations" for the sake of a one-time schema-provisioning step is an unnecessary permanent risk increase for a temporary need.

**3. Tool naming: `chatwoot_<action>`, mirroring `railway_<action>`.**
Consistency with the existing MCP server the founder already uses nightly.

**4. Read tools are unrestricted; write tools (reply, private note, set attributes, add labels) are NOT gated behind extra confirmation inside the MCP itself.**
The MCP is a dumb, faithful wrapper over Chatwoot's API — it does not decide when a write is "safe." That judgment stays with whichever agent/session calls it (the same trust boundary as `railway_set_variable`, `railway_restart`, etc., which are already unguarded destructive-capable tools in the sibling server). A future Hermes auto-tagging pipeline would apply its own approval-queue-style gate before calling `chatwoot_send_reply` for anything customer-facing — that gate belongs in the caller, not the transport.

**5. Custom attribute schema (from the founder's brief, provisioned via task 3.x once an admin token is available):**

Contact-level (`attribute_model: "contact_attribute"`):
`tipo_cliente` (list: lead/prospecto_calificado/cliente/ex_cliente/aliado), `nit_cedula` (text), `empresa` (text), `tipo_contribuyente` (list: persona_natural/SAS/regimen_simple/no_responsable_IVA), `servicio_interes` (list: renta/contabilidad_mensual/creacion_empresa/CFO/facturacion), `plan_actual` (text), `owner_comercial` (text), `hubspot_contact_id` (text — cross-reference, mirrors the pattern `crm_leads.hubspot_contact_id` already uses in Supabase), `supabase_customer_id` (text).

Conversation-level (`attribute_model: "conversation_attribute"`):
`intencion` (list: ventas/soporte/onboarding/cobranza/documento/dian), `prioridad` (list: baja/media/alta/critica), `estado_onboarding` (text), `lead_score` (number), `resumen_ia` (text), `siguiente_accion` (text), `fecha_followup` (date).

## Risks / Trade-offs

- **Schema provisioning is blocked on the founder** (Decision #2) — this change ships the tool and the schema definition, but cannot self-verify end-to-end tonight. Task 3.x is marked accordingly; do not mark it done without a live confirmation.
- The MCP has no test suite beyond what a live `curl`-equivalent smoke test can confirm (same as `railway/`) — Chatwoot's API has no sandbox/mock mode available locally, so tool correctness is verified against the real local Chatwoot instance (account `2`), same as this session did for every fix tonight.
