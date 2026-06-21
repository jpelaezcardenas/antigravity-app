## Context

FASE 3 delivered Agent Critic (deterministic SUM débitos=créditos validation), pgvector + `knowledge_chunks` + `match_knowledge_chunks` RPC, and Approval Queue HTTP routes (`approval_queue_endpoints.py`, prefix `/api/v1/approval-queue`, routes `POST /enqueue|approve|reject` — confirmed live via pre-flight; there is **no** `GET` list route despite `API_REFERENCE.md` documenting one).

**Correction found during Slice 1 implementation (2026-06-21):** `services/approval_queue_service.py` has no real persistence — `enqueue_draft` builds an `ApprovalDecision` object and returns it without writing anywhere, and `approve_draft`/`reject_draft` return a hardcoded placeholder with an explicit code comment ("In a real implementation, this would load the decision from database — For now, we return a placeholder"). There is no `approval_queue` table in Supabase (confirmed via `list_tables`). D1 below originally assumed an existing table to extend additively; Slice 2 must instead **create** `approval_queue` from scratch with `draft_type`/`payload` already in the initial schema, and wire `ApprovalQueueService` to it (replacing the in-memory stub), rather than ALTER an existing table.

Pre-flight against the live Supabase project (read-only `list_tables`/`execute_sql`) found:
- `knowledge_chunks` exists but has 0 rows — the vectorization loop has never run against real data.
- No `tenants`, `dian_xml_documents`, `erp_journal_entries`, or `erp_journal_lines` tables — the Shadow GL does not exist.
- `centinela_alerts` exists (matches `centinela-alerts` spec: similarity-enrichment of alerts) but has 0 rows and no discrepancy source to alert on.
- **Correction found during Slice 2 implementation, task 2.9 (2026-06-21):** `centinela_alerts` has RLS enabled with zero policies — every insert from the backend's anon-key client was rejected (`42501: new row violates row-level security policy`). Same root cause and same fix as the Slice 1/2 RLS corrections already noted (the backend connects with the anon key, not service_role): migration `centinela_alerts_rls_policies` adds policies granting `anon, authenticated, service_role` for select/insert/update, matching the existing pattern instead of introducing a new one.
- **Correction found during Slice 2 implementation, task 2.9 (2026-06-21):** `centinela_alerts.company_id` is a `text` FK into `agent_profiles(company_id)` (FASE 3's per-company config table, e.g. `ctx-001` for Contexia), not a free-text stand-in as originally assumed. The Shadow GL `tenants` table (FASE 4, `uuid` primary key) has no link to `agent_profiles` — these are two separate identity models for the same Cliente Cero company. Fix: migration `tenants_agent_profile_link` adds a nullable `company_id text references agent_profiles(company_id)` column to `tenants`, backfilled to `'ctx-001'` for the Cliente Cero row; `centinela_resolution_service.poll_shadow_gl_discrepancies` resolves `tenant_id` → `tenants.company_id` before inserting into `centinela_alerts`. Reconciling the two identity models fully (e.g. one canonical company/tenant table) is out of scope for this slice — tracked as a Slice 5 follow-up if friction reappears.
- Social Ops already has live tables (`social_command_drafts`, `social_reply_drafts`, `social_sales_drafts`, `service_desk_reply_drafts`) — these are reused, not replaced.
- Separately, an OpenSpec change `hermes-swarm-contexia` exists and is **not archived**; it builds a different system (a local Hermes CLI skill orchestrator under `%LOCALAPPDATA%\hermes\profiles\contexia\`) explicitly out-of-scope for backend/Supabase changes. Left untouched by this change.

Constraints carried over from Ground Truth and `CLAUDE.md`: Contexia is Entidad B (never signs financial statements — every write to ERP/tax filings goes through HITL); Cliente Cero (Contexia SAS) must validate each agent with real data before any external tenant; Stage 11 deployment is mandatory per milestone; money is `BIGINT` minor units + ISO 4217, never float; determinism (Agent Critic) gates the LLM, not the other way around.

## Goals / Non-Goals

**Goals:**
- Stand up the Shadow GL (tenant model + dual DIAN/Siigo ingestion + reconciliation view) as the substrate for Centinela and Radar.
- Implement Centinela's Resolution path end-to-end: detection → LLM draft → Critic → Approval Queue → Siigo write-back → KB vectorization.
- Implement Pulso, Radar, Auditoría as read-mostly/conditional-HITL agents per `AGENTES.md`.
- Implement Taty as an intent router that delegates to the above and escalates sensitive intents.
- Migrate Social Ops onto the FastAPI canonical tables that already exist, fully off n8n.
- Implement Maestro Orchestrator as an in-process async fan-out (no new broker).
- Close the Approval Queue gap: add the missing `GET` list endpoint, generalize `draft_type` so all agents share one gate.
- Validate every agent against Cliente Cero (Contexia SAS) real data before declaring done.

**Non-Goals:**
- Hermes React UI (FASE 5).
- Onboarding any external tenant (FASE 6).
- Schema-based sharding / multi-schema tenancy — single-schema RLS is sufficient at Cliente-Cero scale; revisit if a tenant exceeds ~10M rows or a Centinela scan exceeds 500ms p95.
- Touching or archiving `hermes-swarm-contexia` (separate system, separate decision already made to leave it open).
- Fixing the pre-existing Supabase advisor findings (RLS-disabled tables, SECURITY DEFINER views/functions callable by `anon`, permissive `USING (true)` policies) — these are real and flagged to Dirección, but are a distinct security remediation, not FASE 4 scope.

## Decisions

**D1 — JSONB payload in Approval Queue, not per-draft-type tables.**
The existing pattern (`social_command_drafts`, `social_reply_drafts`, `social_sales_drafts`, ...) is already a one-table-per-type approach and it works operationally — no migration churn to unify them. `approval_queue` itself does not exist yet (FASE 3 shipped only the in-memory-stubbed service + HTTP routes, not a table — see Context correction above), so this change creates it from scratch with a `draft_type` column and JSONB `payload` already in the initial schema, used by Centinela's `tax_correction` and by every other agent's escalations, rather than creating a parallel table per draft type. Alternative considered: a single unified `approval_drafts` table replacing all existing `social_*_drafts` — rejected, because it requires migrating already-wired live tables for no behavioral gain, pure churn.

**D2 — Shadow GL is additive, not a rewrite of existing alert tables.**
`centinela_alerts` (from FASE 3, similarity-enrichment) stays as-is and is fed by the new `dian_xml_documents` / `erp_journal_lines` reconciliation view, rather than replaced. The reconciliation view (`shadow_gl_discrepancies`) is a materialized view refreshed every 15 min via `pg_cron`, not a live join on every request — Centinela's scan stays a fast indexed read.

**D3 — Double-entry enforced at the DB layer via deferred constraint trigger**, not just in application code (Agent Critic). Belt-and-suspenders: Critic blocks bad LLM output before it reaches the queue; the DB trigger blocks any direct SQL (migration, manual fix) from ever creating an unbalanced entry. Alternative (app-only enforcement) rejected — a ledger's core invariant should not depend solely on application discipline.

**D4 — Maestro Orchestrator uses `asyncio.gather` with per-agent timeouts, not Celery/Redis.**
The orchestrator's only job in this phase is parallel `quick_status()` fan-out for the `<500ms` "status" action — an in-process async fan-out is sufficient and avoids adding a broker dependency. Siigo write-back (slow, needs retries) is handled separately by D5, not by the orchestrator.

**D5 — Siigo write-back via a Postgres-backed outbox (`executor_outbox` + `pg_cron` poll), not Celery.**
Write-back is triggered by human approval (minutes-to-hours latency budget already), so a 10s poll interval is invisible. `pg_cron` and Postgres are already provisioned; adding Redis/RabbitMQ for this phase is unjustified operational surface. Revisit if outbox depth exceeds ~1000 sustained.

**D6 — Approval Queue gap is closed by adding the route, not by rewriting `API_REFERENCE.md` to remove it.**
The documented `GET /api/v1/approval-queue` is the correct contract (Hermes UI needs to list pending drafts); it was simply never implemented. This change implements it rather than treating the doc as wrong.

**D7 — LLM cascade order Groq → Cerebras → OpenRouter → Mistral**, matching `agents/llm_engine.py` already in place. Centinela/Taty need sub-1s structured JSON output (Groq); Cerebras/OpenRouter/Mistral are capacity/complexity fallbacks. Critic validates regardless of which provider answered, so cross-provider behavior drift is contained.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| DIAN UBL 2.1 XML parser breaks on schema variants not yet seen | Snapshot-test against ≥20 real Contexia CUFEs in Slice 1 before trusting it for any tenant |
| Siigo write-back hits prod accidentally during testing | Slice 1–2 use Siigo sandbox credentials exclusively; prod Siigo write-back gated behind an explicit env flag, tested only with a Contexia-owned voucher that can be voided |
| `approval_queue` table doesn't exist yet — service was an in-memory stub, not a real persistence gap discovered late | Creating the table with `draft_type`/`payload` from day one in Slice 2 (see Context correction); no existing rows to migrate since none were ever persisted |
| Materialized view refresh lag (15 min) delays anomaly detection | Acceptable for Cliente Cero validation phase; Centinela also exposes an on-demand `REFRESH ... CONCURRENTLY` trigger for manual scans |
| Orchestrator fan-out blocks if one agent's `quick_status()` is accidentally sync | Enforce `async def` via a typed `AgentProtocol`; CI check rejects sync registrations |
| Social Ops migration off n8n silently drops in-flight content | Parallel-run n8n + FastAPI reads for 1 week before cutover; cutover is a flag flip, not a data migration |

## Migration Plan

1. **Slice 1 — Shadow GL substrate**: `tenants` (seed Contexia SAS as Cliente Cero), `dian_xml_documents`, `erp_journal_entries`, `erp_journal_lines` (with deferred balance trigger), `shadow_gl_discrepancies` materialized view. Stage 11 gate: view returns 0 rows cleanly (no real DIAN data ingested yet) — schema-only milestone.
2. **Slice 2 — Centinela Resolution + Approval Queue extension**: DIAN XML ingestion, Siigo journal mirror sync, `approval_queue.draft_type` + `GET` list endpoint, write-back via `executor_outbox`. **Decision (2026-06-21): ingestion starts as a manual upload endpoint (`POST /api/v1/shadow-gl/dian-xml/ingest`, raw XML in the request body), not a live DIAN webhook.** This lets the parser be trained/tested against real Contexia XML files without depending on DIAN/Siigo credentials, which are not yet confirmed available (see Open Questions). The live DIAN webhook listener and the Siigo sandbox/production API connection are deferred to a later phase, once credentials are confirmed; the parser and ingestion logic built now are reused unchanged — only the trigger (manual POST → webhook) changes. Stage 11 gate for this slice is revised accordingly: one real Contexia DIAN XML manually ingested → parsed correctly → reconciliation view reflects it. The "approved → posted to Siigo sandbox" gate moves to the deferred external-connection phase.
3. **Slice 3 — Pulso, Radar, Auditoría**: read endpoints + conditional HITL predicates. Stage 11 gate: all three return valid JSON for Cliente Cero; Radar's conditional HITL fires at least once against seeded high-risk data.
4. **Slice 4 — Taty + Social Ops canonical**: intent router, Telegram webhook, Social Ops endpoints serving the existing tables. Stage 11 gate: Telegram bot responds; Social Ops parallel-run matches n8n output for 1 week before cutover flag flips.
5. **Slice 5 — Maestro Orchestrator + KB integration**: `quick_status()` on each agent, fan-out endpoint, KB lookup wired into Centinela's draft generation. Stage 11 gate: `/hermes/swarm/invoke {action: status}` returns <500ms p95; KB hit measurably reduces LLM calls on repeated anomaly patterns.

**Rollback:** each slice is an independent Railway deploy; `git revert` + redeploy per Stage 11 standard. Schema changes in Slice 1 are additive-only (new tables, no ALTER on existing) — rollback there is a `DROP TABLE` with no data-loss risk since nothing else reads them yet.

## Open Questions

- ~~Siigo sandbox credentials: confirmed available, or do we need to request them before Slice 2 starts?~~ **Resolved 2026-06-21**: not yet available. Slice 2 proceeds with manual XML ingestion only; Siigo journal mirror sync and the live DIAN webhook are deferred to a later phase once credentials are confirmed.
- Who is the named Entidad A for Cliente Cero approvals during testing (whose email goes in `approved_by`)?
- Telegram bot token (`@contexia_bot`) — already provisioned, or part of Slice 4 setup?
- Should the Supabase advisor findings (RLS gaps, `set_hermes_tunnel` callable by anon) be opened as a separate, immediate security change before or in parallel with Slice 1? (Recommended: parallel, not blocking — flagged to Dirección separately.)
