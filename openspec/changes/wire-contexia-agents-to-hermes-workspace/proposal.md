## Why

Hermes Workspace (Nous Research native app) is the central orchestration hub for Contexia's agents, but critical FastAPI agent endpoints (Centinela, Pulso, Radar, Auditoría Sombra) are not yet exposed as MCP tools. This prevents the Hermes Swarm from invoking domain-specific agents programmatically—blocking end-to-end automation of financial operations. By wiring agents as MCP tools, we enable the Swarm's semantic worker roles (centinela-monitor, auditoria-runner) to invoke agents with proper authorization and error handling, completing the Hermes→FastAPI integration loop.

## What Changes

- **New MCP Server**: Create `contexia-mcp-servers/contexia-agents/` (Python, MCP SDK) exposing FastAPI endpoints as 6+ typed tools
  - Tools: `pulso_status`, `centinela_alerts`, `radar_risk`, `auditoria_report`, `shadow_gl_ingest_dian`, `approval_queue_list`
  - Full auth: JWT validation, error handling, response parsing
- **Hermes Workspace Registration**: Register MCP server in Hermes config (`.hermes/config.yaml` or UI)
- **Swarm Role Definitions**: Create 3 new accounting-domain roles in Hermes (`centinela-monitor`, `auditoria-runner`, `resolucion-executor`)
- **Stage 11 Deployment**: Commit to GitHub, verify tools visible in Hermes, document end-to-end invocation

## Capabilities

### New Capabilities
- `mcp-agents-invocation`: MCP tools for invoking Contexia FastAPI agents from Hermes Swarm with typed inputs/outputs, JWT auth, retry logic, and HITL handoff

### Modified Capabilities
<!-- No existing spec-level requirement changes -->

## Impact

- **New Files**: `contexia-mcp-servers/contexia-agents/` (Python package with 6+ tools)
- **Modified**: Hermes Workspace MCP config + Swarm role definitions
- **Dependencies**: MCP SDK 1.2+, httpx, no DB changes
- **Backwards Compatibility**: Non-breaking; new tools are additive
- **Test Surface**: JWT validation, tool input/output schemas, E2E Hermes→FastAPI invocation
