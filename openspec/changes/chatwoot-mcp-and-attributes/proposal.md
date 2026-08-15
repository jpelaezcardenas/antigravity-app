## Why

Chatwoot is Taty's WhatsApp operational front (inbox `1`, "Taty Contadora Amiga 24/7") but today it is opaque to any agent working this repo: every read/write happens as hand-typed `curl` calls against its REST API, with no reusable tool surface. The founder wants the hybrid CRM vision he described (Chatwoot = operational inbox + lightweight CRM layer; HubSpot = commercial pipeline; Supabase = source of truth) to become real, starting with the piece that unblocks everything else: a durable way for agents (Claude Code tonight, Hermes going forward) to read and write Chatwoot data without re-deriving `curl` calls each session.

No MCP registry entry exists for Chatwoot (confirmed live — empty search result). Contexia already has a working pattern for this exact situation: `contexia-mcp-servers/railway/` — a small local Python MCP server wrapping a vendor's REST/GraphQL API, registered in `Projects/.mcp.json`, running on this machine (same data-sovereignty principle as Hermes/GBrain, `ARCHITECTURE.md` decisions #1/#10 — nothing about this needs to run in the cloud, and the API token should not leave the founder's machine).

## What Changes

- New sibling MCP server `contexia-mcp-servers/chatwoot/`, mirroring the `railway/` server's structure exactly: tools for listing/searching conversations, reading messages, reading/writing contact custom attributes, reading/writing conversation custom attributes, adding labels, and sending a reply or private note.
- Define and provision the custom attribute schema on Chatwoot contacts and conversations that the founder specified (`tipo_cliente`, `nit_cedula`, `servicio_interes`, `intencion`, `prioridad`, `resumen_ia`, etc.) via Chatwoot's own Custom Attribute Definitions API, so the fields exist in the UI (filterable/segmentable) before anything tries to write to them.
- Register the new server in `Projects/.mcp.json` so Claude Code can use it starting next session.

## Explicitly Out of Scope (this change)

- The Hermes auto-tagging pipeline itself (LLM classification of intent/NIT/urgency from a conversation, writing those values back via the new MCP tools) — a separate, larger build that depends on this MCP existing first. Tracked as a fast-follow, not started here.
- Any Chatwoot→HubSpot direct integration (Chatwoot already has a native HubSpot app; evaluating it is separate from giving agents API access).
- Two-way sync of any kind — this change only adds read/write TOOLS an agent can call; it does not add an automated sync loop.

## Capabilities

### New Capabilities
- `chatwoot-mcp-server`: a local MCP server exposing Chatwoot's REST API as tools for conversations, contacts, custom attributes, labels, and replies.
- `chatwoot-custom-attribute-schema`: the founder's contact- and conversation-level custom attribute definitions, provisioned in Chatwoot so they exist and are usable (UI + API) before any automation writes to them.

## Impact

- New repo content only in the sibling `contexia-mcp-servers` repo (`chatwoot/`), not `antigravity-app` — same reasoning as `railway/`: it's tooling infrastructure, not product code, and lives where the other local MCP servers already live.
- `Projects/.mcp.json`: one new `chatwoot` entry.
- Chatwoot's own Custom Attribute Definitions (account `2`) gain new records — additive, no risk to existing conversations/contacts/data.
- No changes to `apps/backend` or `apps/chatwoot-bridge` — this is a new, separate read/write surface for agents, not a change to the existing bridge/webhook pipeline that already serves Taty's replies.
