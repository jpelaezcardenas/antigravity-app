# 🚀 SLICE 4: HERMES SWARM ORCHESTRATION + WORKSPACE INTEGRATION

## EN PALABRAS SIMPLES (Para cualquier persona)

### ¿Qué es Contexia?
Contexia es una plataforma que **ve automáticamente lo que hace tu empresa en impuestos, contabilidad y operaciones** — comparando lo que dicen tus documentos (facturas del gobierno DIAN) vs. lo que pusiste en tu sistema (ERP).

### ¿Qué hicimos hasta ahora (Slices 1-3)?
- **Slice 1-2**: Construimos la "visión de rayos X" — la capacidad de ver todos los discrepancias (errores, inconsistencias)
- **Slice 3** (acaba de completarse): Agregamos tres "ojos inteligentes" que miran eso:
  - **Pulso Diario**: Un resumen cada día ("tu salud financiera hoy")
  - **Radar Predictivo**: Una alerta de riesgo ("esto se verá mal en 30 días")
  - **Auditoría Sombra**: Un reporte auditado ("prueba de que revisamos todo")

### ¿Qué es Slice 4 (lo que viene ahora)?
**Hermes Swarm** = Un equipo de agentes inteligentes que trabajan juntos sin parar.

Imagina que tienes un equipo de contadores que:
- No necesitan dormir
- Hablan entre sí automáticamente
- Pueden ser 1, 10, o 100 al mismo tiempo
- Saben exactamente cuándo un problema es real vs. un falso positivo
- **Entrenamiento en vivo**: Cada decisión que toman, aprenden de Cliente Cero para hacerlo mejor

En Contexia, ese equipo es **Hermes**:
- Resuelve automáticamente los alertas pequeños (discrepancias menores)
- Escala a humanos (Entidad A) los problemas grandes
- Mejora con cada caso real de Cliente Cero

---

## PLAN EXHAUSTIVO DE SLICE 4

### Fase 1: Setup & Configuración (Days 1-2)

#### 1.1 Hermes Service Layer
- [ ] Crear `services/hermes_orchestrator.py`
  - `class HermesSwarm`: manage workers, task distribution, state
  - Worker pool: configurable (1-N workers per task type)
  - Task queue: FIFO + priority (critical alerts first)

#### 1.2 Worker Types & Routines
- [ ] **Resolution Worker**: toma `centinela_alerts` → intenta resolver automáticamente
  - Routine: every 5 min, pick top-5 unresolved alerts
  - Action: call `resolution_agent` (Slice 2), capture output
  - Decision: auto-resolve if confidence > 90%, else escalate
  - Workspace checkpoint: log confidence scores in `workspace/hermes/resolution_decisions/`

- [ ] **Reconciliation Worker**: toma discrepancias → propone fixes
  - Routine: every 10 min, batch reconcile small-amount mismatches
  - Action: call `reconciliation_service` (proposed), suggest ERP journal entry
  - Decision: auto-journal if < COP 1M, else show Entidad A
  - Workspace checkpoint: proposed entries in `workspace/hermes/reconciliation_proposals/`

- [ ] **Training Worker**: retrains LLM models from successful resolutions
  - Routine: hourly, collect past 10 auto-resolved cases
  - Action: extract patterns, fine-tune resolution_agent
  - Workspace checkpoint: training logs in `workspace/hermes/training_runs/`

#### 1.3 Workspace Directory Structure
```
workspace/
├── hermes/
│   ├── worker_logs/
│   │   ├── resolution/
│   │   │   └── {timestamp}-batch-{N}.json  (decisions, confidences)
│   │   ├── reconciliation/
│   │   │   └── {timestamp}-proposals.json
│   │   └── training/
│   │       └── {timestamp}-finetune-results.json
│   ├── training_data/
│   │   ├── successful_resolutions.jsonl
│   │   ├── escalated_cases.jsonl
│   │   └── false_positives.jsonl
│   └── cliente_cero_feedback/
│       ├── approved_proposals/
│       └── rejected_proposals/
```

---

### Fase 2: Core Implementation (Days 3-5)

#### 2.1 HermesOrchestrator
```python
class HermesSwarm:
    async def run_workers(self, tenant_id: str):
        """Main loop: spawn workers, collect results, log to workspace"""

        # Worker 1: Resolution
        resolution_results = await self.resolution_worker.run()
        self.log_to_workspace("resolution", resolution_results)

        # Worker 2: Reconciliation
        recon_proposals = await self.reconciliation_worker.run()
        self.log_to_workspace("reconciliation", recon_proposals)

        # Worker 3: Training (async, doesn't block main loop)
        await self.training_worker.schedule_async()

        # Aggregate decisions → approval_queue
        await self.enqueue_decisions(resolution_results, recon_proposals)
```

#### 2.2 Resolution Worker (TDD)
- [ ] Test: Worker picks top-5 unresolved alerts
- [ ] Test: Worker calls resolution_agent, gets confidence
- [ ] Test: Confidence > 90% → auto-resolve + log to workspace
- [ ] Test: Confidence < 90% → escalate + log reason
- [ ] Implement: `resolution_worker.py` with async task loop

#### 2.3 Reconciliation Worker (TDD)
- [ ] Test: Worker batches < COP 1M mismatches
- [ ] Test: Worker generates ERP journal entry proposal
- [ ] Test: Proposal is logged to workspace for Cliente Cero review
- [ ] Test: Approved proposals → auto-journal (if amount < 1M)
- [ ] Implement: `reconciliation_worker.py` with async task loop

#### 2.4 Training Worker (TDD)
- [ ] Test: Worker collects past 10 auto-resolved cases
- [ ] Test: Worker extracts training examples (alert → resolution pattern)
- [ ] Test: Training examples logged to `training_data/successful_resolutions.jsonl`
- [ ] Test: Async doesn't block main loop
- [ ] Implement: `training_worker.py` with async task loop

---

### Fase 3: Workspace Integration (Days 6-7)

#### 3.1 Workspace Checkpoints (No Code Changes, Just Observation)
- [ ] Each worker writes decisions to `workspace/hermes/worker_logs/{type}/{timestamp}.json`
  - Format: `{"decision": "auto-resolve|escalate", "confidence": 0.95, "alert_id": "...", "reason": "..."}`

#### 3.2 Cliente Cero Training Loop
- [ ] Create `workspace/hermes/cliente_cero_feedback/` directory
- [ ] Export daily summary: `workspace/hermes/daily_summary.json`
  - Total alerts processed: N
  - Auto-resolved: M (confidence avg: X%)
  - Escalated: K
  - Training data added: P new examples

- [ ] Cliente Cero reviews and annotates:
  - ✅ "Yes, this resolution was correct"
  - ❌ "No, we'd do it differently"
  - 💭 "Not sure, needs human review"

- [ ] Feedback files: `workspace/hermes/cliente_cero_feedback/{date}-feedback.json`
  ```json
  {
    "alert_id": "...",
    "worker_decision": "auto-resolve",
    "worker_confidence": 0.92,
    "cliente_cero_feedback": "approved",
    "notes": "Good catch on the DIAN mismatch"
  }
  ```

#### 3.3 Feedback Integration (TDD)
- [ ] Test: Load feedback files from workspace
- [ ] Test: High-volume approvals → increase auto-resolve threshold
- [ ] Test: High-volume rejections → escalate similar cases next time
- [ ] Test: "Not sure" → add to training data (data augmentation)
- [ ] Implement: `training_feedback_loop.py` that reads workspace daily

---

### Fase 4: Endpoints & API (Days 8-9)

#### 4.1 New Endpoints (TDD)
- [ ] `POST /api/v1/hermes/invoke` → trigger worker batch
  - Body: `{tenant_id, worker_types: ["resolution", "reconciliation", "training"]}`
  - Response: `{batch_id, workers_started: N, estimated_duration: "2m"}`

- [ ] `GET /api/v1/hermes/batch/{batch_id}` → poll status
  - Response: `{status: "running|completed", results: {...}, workspace_files: [...]}`

- [ ] `POST /api/v1/hermes/approve-proposal/{proposal_id}` → Cliente Cero approves workspace proposal
  - Body: `{approved: true, feedback: "..."}`
  - Action: journal entry → approve_queue, log to workspace feedback

- [ ] `GET /api/v1/hermes/workspace-summary/{date}` → daily stats
  - Response: `{alerts_processed, auto_resolved, escalated, training_data_added, feedback_annotations}`

#### 4.2 Endpoints Registration
- [ ] Create `presentation/hermes_endpoints.py`
- [ ] Register routes in `presentation/router.py`

---

### Fase 5: Full Integration (Days 10-11)

#### 5.1 Worker Scheduler (Background Task)
- [ ] Create background job runner (APScheduler or similar)
- [ ] Schedule resolution worker: every 5 min
- [ ] Schedule reconciliation worker: every 10 min
- [ ] Schedule training worker: every 60 min
- [ ] All workers write to workspace automatically

#### 5.2 E2E Test with Cliente Cero Data
- [ ] Run 24-hour simulation with Cliente Cero historical data
  - Trigger: manually via `POST /api/v1/hermes/invoke`
  - Observe: workspace fills with decisions, logs, training data
  - Verify: all workers complete without errors
  - Measure: latency per worker, confidence distribution, auto-resolve rate

#### 5.3 Workspace Training Loop Validation
- [ ] Manually add feedback annotations to `cliente_cero_feedback/`
- [ ] Trigger feedback loop: `POST /api/v1/hermes/process-feedback`
- [ ] Verify: thresholds adjust, training data augments
- [ ] Workspace should show improvement trend in daily summaries

---

### Fase 6: Stage 11 Deployment (Days 12-13)

#### 6.1 Code Completion
- [ ] All Slice 4 code committed to `main` (backend only)
- [ ] All tests passing: 150+ new tests
- [ ] Zero regressions from Slices 1-3

#### 6.2 Railway Deployment
- [ ] Build succeeds
- [ ] All new endpoints return 200 OK
- [ ] Workers start automatically on deploy
- [ ] Workspace directories created on first run

#### 6.3 Production Verification
- [ ] Manually trigger batch: `POST /api/v1/hermes/invoke`
- [ ] Workspace fills with real decisions (live Cliente Cero data)
- [ ] Training data collected
- [ ] Daily summary shows healthy metrics

#### 6.4 Deployment Report
- [ ] File: `openspec/changes/.../reports/2026-06-XX-slice4-deployment.md`
- [ ] Include: architecture, worker logs from first 24h, workspace evidence, rollback plan

---

### Fase 7: Archive & Close (Day 14)

#### 7.1 Final Checklist
- [ ] All Stage 11 checkpoints ✅
- [ ] Deployment report complete
- [ ] Workspace training loop validated with Cliente Cero
- [ ] Ready for `/opsx:archive`

---

## KEY ARCHITECTURAL DECISIONS

### 1. Workers Are Async, Not Blocking
- Each worker runs independently in a background task
- Main API request loop doesn't wait for workers to finish
- Workspace acts as "dead letter queue" — all decisions logged even if network/DB fails

### 2. Workspace = Ground Truth for Training
- Every decision written to workspace before being acted on
- Client can reject decisions (workspace feedback)
- Feedback used to retrain, not to modify historical data

### 3. Confidence Thresholds Are Adaptive
- Start at 90% (conservative)
- After 100 approved decisions, lower to 85%
- After 10 rejections, raise back to 92%
- Logged in workspace as `threshold_history.jsonl`

### 4. No Database Mutations Without Approval
- Workers *propose* changes, write to workspace
- Only approved changes hit approval_queue → execution
- Rollback: delete workspace file = decision reversed

---

## TESTING STRATEGY

### Unit Tests (per worker)
- Test worker picks correct alerts/proposals
- Test confidence calculation
- Test workspace write (no actual file I/O, mock)

### Integration Tests
- Mock Cliente Cero data (30 day sample)
- Run all 3 workers in parallel
- Verify workspace dir structure
- Verify confidence distribution normal

### E2E Test (Pre-Deploy)
- Real Supabase dev instance + Cliente Cero data
- Trigger workers manually
- Verify workspace fills correctly
- Verify feedback loop works
- Latency check: worker batch < 2 min

---

## SUCCESS SIGNALS (For Slice 4)

✅ Hermes Swarm running 24/7 without errors  
✅ All decisions logged to workspace  
✅ Cliente Cero can review & provide feedback  
✅ Training data accumulates daily  
✅ Auto-resolve rate stable & improving (with feedback)  
✅ Escalation rate < 20% (false positives minimized)  
✅ Deployment in production + all endpoints 200 OK  

---

## DEFERRED TO SLICE 5+

- Advanced scheduling (time-of-day awareness)
- Multi-tenant workspaces (currently single Cliente Cero)
- Model fine-tuning (currently just data collection)
- Prometheus metrics export
- Slack notifications for escalations

---

**Status**: Ready for Slice 4 implementation starting next session.

---

## CONTINUIDAD DESDE SLICE 3

### Commits & Branch State
```
main: commit cbdf25c (docs(slice3): Stage 11 complete)
claude/angry-sutherland-976d5d: commit cbdf25c (synced after merge)
```

### Tests Passing
- Slice 1+2+3: 122 passing, 1 skipped, 0 failures

### Endpoints Live in Production
- GET /api/v1/agents/pulso-diario/summary → 200 OK
- GET /api/v1/agents/radar-predictivo/risk-score → 200 OK
- POST /api/v1/agents/auditoria-sombra/report → 200 OK

### Next: Slice 4 (Hermes) following this plan
