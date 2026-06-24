## Why

FASE 3 shipped the deterministic plumbing (Agent Critic, pgvector, decision vectorization, single-draft-type Approval Queue) but none of the 9 agents in `AGENTES.md` actually run against real data yet. Centinela's anomaly detection assumes a DIAN-vs-Siigo discrepancy source that does not exist in the database — there is no Shadow GL. Pulso, Radar, Auditoría, Taty, Social Ops, and the Maestro Orchestrator are documented (catalog + API_REFERENCE.md) but unimplemented. Cliente Cero cannot validate anything end-to-end until this gap closes. This change builds the Shadow GL and implements the 9 agents incrementally, each gated by Stage 11.

## What Changes

- Build the Shadow GL: tenant model, DIAN XML (UBL 2.1) ingestion, Siigo journal mirror, and a discrepancy reconciliation view — the data substrate every Tier-1 agent reads from.
- Implement Centinela's Resolution path: anomaly → draft → Agent Critic → Approval Queue → Siigo write-back → KB vectorization. (Centinela's alert/similarity-enrichment behavior already exists in `centinela-alerts`; this adds the part that proposes and executes corrections.)
- Implement Pulso Diario, Radar Predictivo, and Auditoría Sombra as read-mostly agents with their HITL rules coded per `AGENTES.md`.
- Implement Taty as a conversational router that delegates to the above and escalates sensitive intents to Approval Queue.
- Migrate Social Ops (Ideas, Lead Reply, Sales Closure, Metrics) onto the existing `social_*_drafts` tables in FastAPI canonical, off n8n.
- Implement the Maestro Orchestrator: parallel fan-out/fan-in over agent `quick_status()` calls, <500ms budget, graceful partial-failure.
- **Modify Approval Queue**: add a `GET` list endpoint (currently missing — `API_REFERENCE.md` documents one that was never built) and generalize enqueue to accept `draft_type` beyond `tax_correction` so Centinela, Social Ops, and Taty share one gate. **BREAKING**: enqueue payload shape changes from implicit tax-correction-only to `{draft_type, payload, rationale}`.

## Capabilities

### New Capabilities
- `shadow-gl-ingestion`: tenants, DIAN XML UBL 2.1 parser, Siigo journal mirror, reconciliation view
- `centinela-resolution`: discrepancy → draft → Critic → queue → write-back → vectorize
- `pulso-diario`: daily flux-analysis summary (read-only)
- `radar-predictivo`: risk scoring + cashflow forecast (conditional HITL on critical score)
- `auditoria-sombra`: continuous audit PDF report (conditional HITL on signature)
- `taty-conversational`: intent router + Telegram webhook + escalation to queue
- `social-ops-canonical`: Ideas/Reply/Sales/Metrics agents on existing tables, off n8n
- `maestro-orchestrator`: parallel swarm status fan-out/fan-in

### Modified Capabilities
- `approval-queue`: add `GET /api/v1/approval-queue` list endpoint; generalize `draft_type` handling beyond tax corrections

## Impact

- New tables: `tenants`, `dian_xml_documents`, `erp_journal_entries`, `erp_journal_lines`, `executor_outbox`. Reuses existing `social_*_drafts` and `centinela_alerts` tables.
- Modified: `apps/backend/presentation/approval_queue_endpoints.py`, `apps/backend/services/orchestrator_service.py` (currently a stub).
- New integrations: DIAN webhook, Siigo REST API (read + write-back), Telegram webhook for Taty.
- Out of scope: Hermes React UI (FASE 5), external tenant onboarding (FASE 6), schema-based sharding, the unrelated `hermes-swarm-contexia` change (Hermes CLI local orchestrator — different system, left untouched).
