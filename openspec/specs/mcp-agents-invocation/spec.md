# mcp-agents-invocation Specification

## Purpose
TBD - created by archiving change wire-contexia-agents-to-hermes-workspace. Update Purpose after archive.
## Requirements
### Requirement: MCP Server Exposes Contexia Agents as Tools
The MCP server (`contexia-agents`) SHALL expose 6+ FastAPI agent endpoints as typed MCP tools with clear input/output schemas. Each tool SHALL map 1:1 to a backend agent endpoint.

#### Scenario: Tool definition includes input/output schemas
- **WHEN** MCP client (Hermes Swarm) introspects the MCP server
- **THEN** server returns 6+ tools with Zod/Pydantic-derived JSON schemas for inputs and outputs
- **AND** each tool has a description, example use case, and response time estimate

#### Scenario: Tool payload matches FastAPI endpoint contract
- **WHEN** tool is invoked with valid inputs
- **THEN** request is transformed to match FastAPI endpoint signature
- **AND** response is parsed and typed according to tool output schema
- **AND** invalid inputs trigger early validation error before HTTP call

---

### Requirement: JWT Bearer Token Authentication
Every MCP tool SHALL validate a JWT bearer token before invoking the backend. The token SHALL be read from the local `.env` file (`CONTEXIA_AGENTS_API_TOKEN`). Invalid or expired tokens SHALL trigger a clear error response.

#### Scenario: Valid token accepts request
- **WHEN** tool is invoked with a valid, non-expired JWT token in env
- **THEN** HTTP request to FastAPI endpoint includes `Authorization: Bearer <token>`
- **AND** endpoint accepts the request (returns 2xx)
- **AND** tool returns parsed response to Hermes

#### Scenario: Expired token triggers re-login
- **WHEN** tool is invoked and JWT has expired (`exp` claim < current time)
- **THEN** tool returns error: "Token expired. Please re-login in Hermes and update `.env`"
- **AND** no HTTP request is made (fail fast)

#### Scenario: Missing token returns setup error
- **WHEN** tool is invoked and `CONTEXIA_AGENTS_API_TOKEN` is not in `.env`
- **THEN** tool returns error: "Setup error: `CONTEXIA_AGENTS_API_TOKEN` not found in `.env`. See README for setup."
- **AND** no HTTP request is made

---

### Requirement: Retry Logic for Transient Failures
MCP tools SHALL retry HTTP requests to FastAPI on 5xx server errors (502, 503, 504) with exponential backoff. Auth errors (401, 403) SHALL fail immediately without retry.

#### Scenario: 5xx error retries with backoff
- **WHEN** FastAPI endpoint returns 502 Bad Gateway
- **THEN** tool retries immediately (attempt 2)
- **AND** if attempt 2 also fails with 5xx, retries after 2s (attempt 3)
- **AND** if attempt 3 also fails with 5xx, retries after 4s (attempt 4)
- **AND** after 3 failed attempts, tool returns error: "Service temporarily unavailable. Please try again."

#### Scenario: 401 auth error fails immediately
- **WHEN** FastAPI endpoint returns 401 Unauthorized
- **THEN** tool does NOT retry
- **AND** tool returns error: "Authentication failed. Token may be invalid or expired."

#### Scenario: 4xx client error fails immediately
- **WHEN** FastAPI endpoint returns 400 Bad Request (invalid input)
- **THEN** tool does NOT retry
- **AND** tool returns error with details from FastAPI response

---

### Requirement: Response Parsing and Type Validation
MCP tools SHALL parse FastAPI JSON responses and validate against their output schema before returning to Hermes. Malformed or unexpected responses SHALL trigger a clear error.

#### Scenario: Valid JSON response passes validation
- **WHEN** FastAPI endpoint returns 200 with valid JSON
- **THEN** response is parsed and validated against output schema
- **AND** tool returns the response to Hermes as-is (no transformation)
- **AND** Hermes UI displays the response in the appropriate format

#### Scenario: Malformed JSON triggers validation error
- **WHEN** FastAPI endpoint returns 200 with invalid JSON (e.g., truncated)
- **THEN** tool catches JSON decode error
- **AND** tool returns error: "Invalid response from agent. Please contact support."

#### Scenario: Unexpected response structure is rejected
- **WHEN** FastAPI endpoint returns 200 with valid JSON but mismatched schema (e.g., missing required field)
- **THEN** tool validates against output schema
- **AND** if validation fails, tool returns error: "Unexpected response structure from agent"
- **AND** error includes the unexpected field names for debugging

---

### Requirement: Six Core Agent Tools
The MCP server SHALL expose six primary tools corresponding to key Contexia agents. Each tool SHALL have a docstring, input schema, output schema, and error handling.

#### Scenario: pulso_status tool returns operational state
- **WHEN** Hermes Swarm invokes `pulso_status` with tenant_id
- **THEN** tool calls `GET /api/v1/agents/pulso-diario/summary?tenant_id=<uuid>`
- **AND** returns structured response with daily alerts, obligaciones, liquidez, proyecciones
- **AND** response includes timestamp (datetime)

#### Scenario: centinela_alerts tool returns tax alerts
- **WHEN** Hermes Swarm invokes `centinela_alerts` with tenant_id
- **THEN** tool calls `GET /api/v1/centinela?tenant_id=<uuid>`
- **AND** returns list of DIAN alerts, vencimientos, discrepancias
- **AND** each alert includes severity, due_date, recommended_action

#### Scenario: radar_risk tool returns predictive risk
- **WHEN** Hermes Swarm invokes `radar_risk` with tenant_id
- **THEN** tool calls `GET /api/v1/radar?tenant_id=<uuid>`
- **AND** returns structured risk forecast with impuestos_futuros, liquidity_projection, anomalies
- **AND** each forecast includes confidence_score (0-100)

#### Scenario: auditoria_report tool generates shadow audit
- **WHEN** Hermes Swarm invokes `auditoria_report` with tenant_id, date_range
- **THEN** tool calls `POST /api/v1/wizard/auditoria-sombra` with request body
- **AND** returns PDF link and summary of discrepancias found
- **AND** includes count of matched transactions and unmatched items

#### Scenario: shadow_gl_ingest_dian tool ingests tax documents
- **WHEN** Hermes Swarm invokes `shadow_gl_ingest_dian` with tenant_id, xml_dian_files
- **THEN** tool calls `POST /api/v1/shadow-gl/dian-xml/ingest` with file batch
- **AND** returns ingestion summary (parsed, errors, matched_count)

#### Scenario: approval_queue_list tool shows pending approvals
- **WHEN** Hermes Swarm invokes `approval_queue_list` with tenant_id
- **THEN** tool calls `GET /api/v1/approval-queue?tenant_id=<uuid>`
- **AND** returns list of pending drafts with status, created_at, draft_type
- **AND** each draft includes payload for Hermes to display context

---

### Requirement: Graceful Timeout Handling
MCP tools SHALL enforce HTTP timeouts and return clear errors if requests exceed the timeout window. The default timeout SHALL be 30 seconds.

#### Scenario: Request timeout returns error
- **WHEN** FastAPI endpoint does not respond within 30s
- **THEN** HTTP client raises timeout exception
- **AND** tool returns error: "Request timed out. Agent is busy or network is slow. Please retry in a moment."
- **AND** no retry is attempted for timeout errors

---

### Requirement: Local-Only Execution (Data Sovereignty)
The MCP server SHALL run exclusively on the user's local machine (WSL). It SHALL NOT accept remote connections or be deployable to cloud infrastructure. Configuration SHALL enforce this constraint.

#### Scenario: Server binds to localhost only
- **WHEN** MCP server starts
- **THEN** server listens on `127.0.0.1` (not `0.0.0.0`)
- **AND** README explicitly states "local WSL only"
- **AND** .env.example does NOT include cloud service variables

#### Scenario: Documentation warns against cloud deployment
- **WHEN** user reads README or setup guide
- **THEN** documentation clearly states: "Hermes Workspace and this MCP server are designed for local, on-premise execution for data sovereignty. Do NOT deploy to cloud VPS."

---

### Requirement: MCP Tool Registration in Hermes
The MCP server SHALL be registered in Hermes Workspace configuration so Swarm roles can discover and invoke tools. Tools SHALL appear in Hermes UI tool picker.

#### Scenario: Server is discoverable via Hermes MCP config
- **WHEN** user adds MCP server to `~/.hermes/config.yaml`
- **THEN** Hermes detects the new server and loads its tools
- **AND** Swarm roles can reference the tools by name in prompts/tasks

#### Scenario: Tool appears in Hermes UI
- **WHEN** user opens Hermes Workspace and views the tool library
- **THEN** all 6+ Contexia agent tools are listed with names, descriptions, and example inputs

