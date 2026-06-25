## Context

Hermes Workspace (Nous Research native, WSL port 3000) is the operational hub for Contexia's agents. It orchestrates 10 semantic Swarm roles (orchestrator, builder, reviewer, qa, researcher, ops-watch, km-agent, maintainer, strategist, inbox-triage) via gateway (port 8642) and dashboard (port 9119). Currently, MCP servers are registered (e.g., `contexia-railway` for Railway operations), but Contexia's own FastAPI agents are not exposed as MCP tools. This blocks the Swarm from invoking agents programmatically and completing the Hermes orchestration loop.

**Current state:**
- Backend Railway: ✅ healthy, `/api/v1/approval-queue` endpoint vivo, JWT auth functional
- Hermes Workspace: ✅ native MCP client, 10 roles defined, MCP registration infrastructure in place
- MCP ecosystem: ✅ `contexia-railway` (Python + MCP SDK) serves as architectural reference
- Agent exposure: ❌ no MCP server for FastAPI agents

**Constraints:**
- Hermes Workspace runs **locally (WSL only)**, never cloud, for data sovereignty
- MCP server must read token from env, never hardcode
- All agent tools must validate JWT and handle expiry gracefully
- HITL (Human-in-the-Loop) approval queue is mandatory for sensitive operations

## Goals / Non-Goals

**Goals:**
1. Create a Python MCP server (`contexia-mcp-servers/contexia-agents/`) that exposes 6+ typed FastAPI agent tools
2. Implement JWT validation and bearer token auth (reuse Railway login)
3. Register MCP server in Hermes Workspace config
4. Define 3 new Swarm roles for accounting domain (centinela-monitor, auditoria-runner, resolucion-executor)
5. Enable end-to-end Hermes Swarm → MCP tool → FastAPI endpoint → response flow
6. Stage 11 deployment: commit, verify, report

**Non-Goals:**
- Do not modify FastAPI agent endpoints (they remain unchanged)
- Do not build Hermes UI frontend (Hermes is native Nous app)
- Do not change Supabase RLS or HITL queue behavior
- Do not deploy MCP server to cloud; local WSL only
- Do not add real-time WebSocket tools (HTTP request/response only)

## Decisions

### **D1: Python + MCP SDK (vs. JavaScript/TypeScript)**
**Decision:** Use Python 3.10+ with MCP SDK 1.2+, following contexia-railway pattern.

**Rationale:**
- Contexia backend is Python (FastAPI), so tool implementations can reuse utilities/auth logic from antigravity-app
- MCP SDK is language-agnostic; Python has solid typing support
- Mirror contexia-railway (proven pattern) reduces decision fatigue

**Alternative considered:** TypeScript/Node.js MCP server → harder to reuse FastAPI code, introduces JS ecosystem dependency

---

### **D2: Tool Definitions as Separate Modules**
**Decision:** Organize tools in `tools/` subdirectory with one file per agent domain.
- `tools/pulso.py` → pulso_status, pulso_summary
- `tools/centinela.py` → centinela_alerts, centinela_status
- `tools/audit.py` → auditoria_report, shadow_gl_ingest_dian
- `tools/queue.py` → approval_queue_list

**Rationale:**
- Clear separation of concerns; each tool file owns its agent domain
- Easier to add tools later (new file = new domain)
- Tests can isolate per-domain tool behavior

**Alternative considered:** Monolithic `tools.py` with all 6+ tools → harder to maintain, test, extend

---

### **D3: JWT Validation at Tool Layer (not server layer)**
**Decision:** Each tool validates its JWT before calling FastAPI. No global auth middleware in MCP server.

**Rationale:**
- MCP spec does not define standard auth layer; tools are stateless
- Allows per-tool auth logic (e.g., some tools read-only, others require HITL approval)
- Matches contexia-railway pattern (each API call validates token)
- Graceful error handling per tool

**Alternative considered:** Global MCP server auth → would require MCP client to pass token in request header, adding complexity

---

### **D4: Retry Logic for Transient Failures**
**Decision:** Implement exponential backoff retry (3 attempts, 1s/2s/4s) for HTTP 5xx errors. Fail fast on 4xx auth errors.

**Rationale:**
- Railway deployments can have brief downtime or slow starts
- HITL queue operations must be reliable (user is waiting)
- Auth errors (401, 403) are not retryable; user must re-login

**Alternative considered:** No retry → higher chance of false negatives in production

---

### **D5: Response Parsing & Type Validation**
**Decision:** Use Pydantic models for all tool inputs/outputs. Validate FastAPI response before returning to Hermes.

**Rationale:**
- Type safety; prevents hallucinations (agent critic pattern from APM Nominal model)
- Hermes UI can rely on tool signatures
- Early error detection (JSON schema mismatch during dev)

**Alternative considered:** Raw JSON response → harder to debug, less IDE support

---

### **D6: Local Env Config (not cloud secrets)**
**Decision:** Token read from `.env` file (user's local machine). Never commit `.env`.

**Rationale:**
- Hermes runs local, not cloud VPS
- Simplifies setup; user adds `CONTEXIA_AGENTS_API_TOKEN=<jwt>` to local `.env`
- Matches contexia-railway pattern

**Alternative considered:** Keeper integration → overkill for local; `.env` is standard for local dev

---

## Architecture: Tool Classification (A/B Boundary)

**Context:** Contexia has dual governance (Entidad A regulatory + Entidad B tech). Tools exposed to Hermes Swarm must respect this boundary explicitly. Two tool classes:

### **LADO A — Tools Finas (Fine-grained, Nous orchestrates freely)**
- **Invariant:** Read-only, no side effects, idempotent, can be called 1000× safely
- **Use case:** Hermes user asks "what's the risk?", "show alerts", "check balance" → Nous combines results
- **Examples:**
  - `pulso_daily_summary` → GET /api/v1/agents/pulso-diario/summary (status/liquidity)
  - `centinela_list_alerts` → GET /api/v1/centinela (alerts)
  - `radar_risk_score` → GET /api/v1/agents/radar-predictivo/risk-score (forecast)
  - `approval_queue_list` → GET /api/v1/approval-queue (view pending, NO approve)
  - `shadow_gl_query` → GET (read discrepancies, NO ingest)

### **LADO B — Tools Gruesas (Coarse-grained, Maestro Contexia orchestrates sequence)**
- **Invariant:** Any side effect (write to ledger/ERP), must chain through HITL approval, auditable sequence
- **Use case:** Hermes user asks "fix this discrepancy" → encola a Maestro → Maestro runs fixed sequence → Entidad A human approves → executor writes
- **Examples:**
  - `run_reconciliation_cycle` → Centinela poll → detect mismatch → draft → critic → enqueue (1 tool = entire sequence)
  - `ingest_dian_batch` → parse XML → upsert → audit (single tool, deterministic)
  - `execute_approved_draft` → read approved_draft → write-back to Siigo ERP (irreversible, post-HITL only)

### **Invariant: Nous Never Approves**
- ✅ Nous (LLM Swarm) can READ, ANALYZE, RECOMMEND
- ❌ Nous CANNOT write, approve, or execute Lado B tools without human in-the-loop
- Human (Entidad A) remains the only decision-maker for compliance/regulatory actions
- This preserves legal accountability

### **Tool Boundary Rules**
1. If a tool has ANY write effect → classify as Lado B
2. If a tool can change ledger/ERP/approval state → classify as Lado B
3. If a tool MUST be approved before executing → classify as Lado B
4. If a tool is idempotent read 1000× → classify as Lado A
5. When in doubt: safe choice is Lado B (adds HITL gate)

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **JWT expiry during long Swarm task** → tool fails mid-execution | Tool returns clear error message; Hermes UI prompts user to re-login and retry. Document token lifespan (24h) in README. |
| **FastAPI endpoint latency (3-5s)** → Hermes UI feels slow | Add tool docstring: "⏱️ ~3s response time" so user expectations are set. Hermes UI can show spinner. |
| **Railway downtime during deploy** → tool returns 502 | Retry logic handles transient 5xx. User sees "service temporarily unavailable" after 3 failed attempts. |
| **Conflicting tool names** (e.g., `audit_report` vs `auditoria_report`) | Adopt Spanish+English hybrid naming (e.g., `centinela_alerts` for Centinela Fiscal). Document naming convention in README. |
| **Hermes Swarm role config drift** → MCP tools registered but roles don't use them | Version Swarm role definitions in code; Stage 11 includes role config in deployment report. |

## Migration Plan

1. **Phase 1 (Setup):** Create MCP server directory, install deps, write tools
2. **Phase 2 (Auth & Testing):** Implement JWT validation, write unit + E2E tests
3. **Phase 3 (Registration):** Register server in Hermes config, verify MCP inspector sees tools
4. **Phase 4 (Swarm Integration):** Define 3 new Swarm roles, test tool invocation from Hermes UI
5. **Phase 5 (Stage 11):** Commit to GitHub, deploy, write report, archive change

**Rollback:** If Stage 11 fails, remove MCP registration from Hermes config; MCP server code remains in repo for later fix.

## Open Questions

1. **Should MCP server be in `contexia-mcp-servers/` or in `antigravity-app/`?** → Recommend `contexia-mcp-servers/contexia-agents/` to separate concerns (app code vs. MCP glue)
2. **How to handle agent token refresh?** → Defer to Phase 2; for now, user provides fresh token in `.env` if expired
3. **Which FastAPI endpoints map to which tools?** → Define in specs/ during ADDED requirements phase
