# 🗺️ ROADMAP COMPLETO: FASE 4 — Orquestación de 9 Agentes + Hermes Workspace

**Versión:** 1.0  
**Fecha:** 2026-06-21  
**Destinatario:** Próximo chat Claude Code (FASE 4 Implementation)  
**Estado Previo:** FASE 3 completada (Agent Critic + pgvector + Vectorización = 53/53 tasks ✅)  
**Propósito:** Pasar del MVP escalable (FASE 3) a la **Orquestación Completa de 9 Agentes** bajo Ground Truth v2.0 + Modelo APM Nominal + Hermes Workspace + Cliente Cero

---

## 📋 INSTRUCCIÓN PARA INICIAR NUEVO CHAT

### PASO 1: Adjuntar estos archivos al inicio del chat

```
@"C:\Users\contexia\.claude\CLAUDE.md"
@"C:\Users\contexia\Projects\antigravity-app\CLAUDE.md"
@"C:\Users\contexia\Projects\antigravity-app\AGENTS.md"
@"C:\Users\contexia\Projects\antigravity-app\AGENTES.md"
@"C:\Users\contexia\Projects\antigravity-app\openspec\config.yaml"
@"C:\Users\contexia\Projects\antigravity-app\DEPLOYMENT_STAGE\DEPLOYMENT_STAGE.md"
@"C:\Users\contexia\Projects\antigravity-app\ai-specs\openspec-deployment-standard\checklist-railway.md"
@"C:\Users\contexia\Projects\antigravity-app\openspec\changes\add-pgvector-agent-critic-phase-3\reports\2026-06-21-deployment.md"
@"C:\Users\contexia\Projects\antigravity-app\ROADMAP_AGENTES_FASE4.md"
```

### PASO 2: Mensaje inicial para el nuevo chat

```
PROYECTO: Contexia — Entidad B (Agentic Performance Management para PyMEs colombianas)
ETAPA: FASE 4 — Orquestación Completa de 9 Agentes + Hermes Workspace
FECHA: 2026-06-21 (sesión anterior) → 2026-06-22+ (este chat)
REPO: antigravity-app (FastAPI/Railway + Supabase + Hermes Workspace)

ESTADO PREVIO (FASE 3 - CERRADA):
✅ Agent Critic: Validador determinista (SUM débitos = SUM créditos)
✅ pgvector: Vector similarity search en Supabase (reemplazó memory fallback)
✅ Decision Vectorization: Decisiones aprobadas → embeddings → knowledge_chunks
✅ E2E Test: Cliente Cero full loop (Centinela → Critic → ApprovalQueue → Vectorization → KB)
✅ Stage 11: Deployed a Railway, commit a53d0c9, 19/19 tests pass

ESTADO ACTUAL (este chat):
📊 9 Agentes definidos en AGENTES.md (catálogo v2.0):
  TIER 1 (Core APM Nominal):
    1. Centinela Fiscal (Transaction Patrol + Resolution)
    2. Pulso Diario (Flux Analysis)
    3. Radar Predictivo (Pattern Recognition + Forecasting)
    4. Auditoría Sombra (Continuous Audit)
  TIER 2 (Conversacional):
    5. Taty (Conversational Operator + Telegram 24/7)
  TIER 3 (Social Ops heredado):
    6. Social Ops (Ideas, Lead Reply, Sales Draft, Metrics)
  TIER 4 (KB):
    7. Knowledge Base (RAG + pgvector, aprendizaje compuesto)
  TIER 5 (Orquestación):
    8. Maestro Orchestrator (Swarm Coordinator, paralleliza 5+ agentes)
  TIER 6 (HITL):
    7. Approval Queue (Central gate, obligatorio para acciones sensibles)

BLOQUEADOR ACTUAL:
❌ Agentes 1-8 tienen especificaciones en AGENTES.md pero NO están implementados
❌ Hermes Workspace sin endpoints canónicos para cada agente
❌ Sin orquestación: Agentes aislados, no hay "swarm"
❌ Sin telemetría/auditoría centralizada
❌ Social Ops heredado (n8n legacy) → necesita migración a FastAPI canónico

OBJETIVO FASE 4:
✅ Implementar 9 agentes (uno por uno, baby steps)
✅ Endpoints canónicos: GET/POST /api/v1/{centinela,pulso,radar,auditoría,social-ops,kb,approval-queue,orchestrator}
✅ HITL rules coded: qué requiere aprobación, qué no
✅ Cliente Cero testea cada agente con datos reales
✅ Knowledge Base crece (decisiones aprobadas → vectorizadas → reutilizables)
✅ Hermes Workspace operativo: dashboard + approval queue + swarm status
✅ Stage 11 deploy a Railway + reporte final

RUNWAY (estimado):
  FASE 4a (Agentes 1-4, Core APM): 5-7 días
  FASE 4b (Agentes 5-6, Conversacional + Social): 3-4 días
  FASE 4c (Agentes 7-8, KB + Orchestrator): 2-3 días
  FASE 4d (Hermes Workspace UI + E2E): 2-3 días
  FASE 4e (Stage 11 Deployment): 1 día
  TOTAL: ~13-20 días (julio 2026 target)

SIGUIENTE DESPUÉS FASE 4:
  FASE 5: Hermes Workspace UI (React componentes, dashboards)
  FASE 6: Cliente externo #1 (Copiloto Contratos EAFIT, con sandboxing)
  FASE 7: Sales + Onboarding automation

---

INSTRUCCIONES OBLIGATORIAS PARA EL AGENTE FASE 4:
1. LEE Ground Truth + CLAUDE.md + AGENTS.md + AGENTES.md antes de tocar código
2. VERIFICA qué agentes están implementados (Centinela? Pulso?) vs especificados
3. PROPÓN OpenSpec change: "hermes-swarm-contexia-phase4-agents"
4. DISEÑA tasks.md incremental: Agent 1 (Centinela) → Agent 2 (Pulso) → ... → Agent 8 (Orchestrator)
5. ANTES DE CODE: Verifica Supabase (pgvector ready?), Railway env vars (LLM keys?), test data (Cliente Cero loaded?)
6. IMPLEMENTA con baby steps: endpoint + service + tests + Stage 11 (no mega-commits)
7. INTEGRA con Approval Queue: Agent → draft → HITL gate → ejecución
8. VECTORIZA decisiones aprobadas: cada aprobación → embedding en knowledge_chunks
9. TESTA E2E: Cliente Cero + full loop (Agent → Approval → Vectorization → KB)
10. DEPLOYA: Stage 11 obligatorio, commit + Railway rebuild + reporte

RECURSOS DISPONIBLES:
✅ Contexto: AGENTES.md (9 agentes definidos)
✅ Modelos: APM Nominal (Nominal y Contexia_ Análisis Tecnológico.md)
✅ Infraestructura: FastAPI (/api/v1/*), Supabase (pgvector), Railway (175a), Hermes Workspace
✅ HITL: Approval Queue ya existe (FASE 3), extiende para todos los agentes
✅ Vectorización: Embeddings service ya existe (FASE 3)
✅ Testing: Cliente Cero (datos reales de Contexia)
✅ OpenSpec: spec-driven workflow, 11 stages, obligatorio Stage 11

HERRAMIENTAS & APIs DISPONIBLES:
- FastAPI (backend)
- Supabase (DB + pgvector + RLS + email)
- Railway (deploy + env vars + logs)
- Telegram API (Taty)
- Siigo API (ERP, para Centinela)
- DIAN webhook (facturas)
- OpenAI embedding (o Cerebras fallback)
- Groq/Cerebras inference (para LLM agents: Radar, Taty, Social Ops)
- n8n (legacy, pero puede integrar si necesario)

ESTADO CONOCIDO (NO CAMBIAR):
✅ Contexia es Entidad B (no firma nada)
✅ Hermes Workspace es centro operativo (NO Bunker)
✅ Cliente Cero = Contexia (primero productivo antes de externos)
✅ HITL obligatorio en sensible (asientos, publicaciones, /ops)
✅ Stage 11 deployment es NO negociable
✅ OpenSpec es fuente de verdad (documentación primero, código segundo)
```

### PASO 3: Ceremonia OpenSpec para el Agente FASE 4

El nuevo agente debe ejecutar EXACTAMENTE esto (copia-pega, no improvisar):

```
CEREMONIA OPENSPEC FASE 4:

1. LEE Ground Truth (5 min)
   - Contexia es Entidad B tecnológica
   - Hermes Workspace = centro operativo
   - Ground Truth v2.0 es máxima referencia
   
2. LEE AGENTES.md (10 min)
   - 9 agentes definidos (1 Centinela, 2 Pulso, 3 Radar, 4 Auditoría, 5 Taty, 6 Social Ops, 7 KB, 8 Orchestrator, 9 Approval Queue)
   - HITL rules claras (qué requiere aprobación)
   - Cliente Cero antes de externos
   
3. VERIFICA estado actual (5 min)
   - ¿Cuáles de los 9 agentes EXISTEN en código?
   - ¿Cuáles son SOLO especificación?
   - ¿Qué endpoints falta implementar?
   
4. PROPÓN OpenSpec change (10 min)
   - Name: "hermes-swarm-contexia-phase4-agents"
   - Proposal: "Implementar 9 agentes bajo orquestación centralizada"
   - In Scope: Agents 1-8 (implementar), Approval Queue (extender), Hermes UI (menus/dashboards)
   - Out Scope: Hermes React refactor (es Phase 5), cliente externo (es Phase 6)
   
5. DISEÑA tasks.md (15 min)
   - Agent 1 (Centinela): endpoint + service + HITL + tests
   - Agent 2 (Pulso): endpoint + service + tests
   - ... (similar para agentes 3-8)
   - Integración Approval Queue (todos los agentes)
   - Vectorización (decisiones aprobadas → KB)
   - E2E test (Cliente Cero)
   - Stage 11 deploy
   
6. VERIFICA PRE-REQUISITOS (5 min)
   ✅ pgvector extension habilitada? (SELECT * FROM pg_extension WHERE extname='vector';)
   ✅ knowledge_chunks table existe? (SELECT COUNT(*) FROM knowledge_chunks;)
   ✅ match_knowledge_chunks RPC? (SELECT * FROM match_knowledge_chunks([...]);)
   ✅ OPENAI_API_KEY en Railway? (echo $OPENAI_API_KEY en shell)
   ✅ Cliente Cero data loaded? (SELECT COUNT(*) FROM [cliente_cero_tables];)
   ✅ Approval Queue endpoints existentes? (GET /api/v1/approval-queue/*)
   
7. INICIA /opsx:propose (OpenSpec)
   - Genera proposal.md, design.md, specs/*, tasks.md automáticamente
   - Tú revisa, ajusta si necesario, luego /opsx:apply
```

---

## 🎯 ROADMAP FASE 4 (DETALLADO)

### HITO 1: Agentes Core (APM Nominal) — Semana 1

#### Agent 1: Centinela Fiscal (Transaction Patrol + Resolution)
**Responsabilidad:** Monitoreo DIAN vs ERP, generación de ajustes contables  
**Endpoint:** `GET /api/v1/centinela` (lista anomalías) + `POST /centinela/resolve` (genera draft)  
**Entrada:** dian_xml + erp_journal_lines  
**Salida:** tax_correction_drafts (pending_approval en Approval Queue)  
**HITL:** ✅ SÍ (Entidad A aprueba en Hermes)  
**Test:** E2E cliente_cero (factura DIAN $10M sin asiento)  
**Telemetría:** log cada anomalía detectada (DIAN ID, monto, discrepancia, timestamp)  
**Integración KB:** Si draft aprobado, vectoriza "¿por qué aprobamos este ajuste?" para futuros matches

#### Agent 2: Pulso Diario (Flux Analysis)
**Responsabilidad:** Resumen operativo diario (caja, vencimientos, variaciones)  
**Endpoint:** `GET /api/v1/pulso` → retorna JSON + narrativa  
**Entrada:** transactions (24h), tax_alerts, bank_feeds  
**Salida:** JSON {caja_disponible, vencimientos_hoy, variaciones_detectadas, narrative_summary}  
**HITL:** ❌ NO (solo lectura, Entidad A revisa en Hermes dashboard)  
**Test:** Verifica narrativa coherente (ej: "Caja bajó $500K porque X")  
**Cadencia:** Diaria (9 AM, cron job)  
**Integración KB:** Usa KB para explicar variaciones ("el mes pasado pasó algo similar, fue por Y")

#### Agent 3: Radar Predictivo (Pattern Recognition + Forecasting)
**Responsabilidad:** Riesgos fiscales/negocio, proyecciones 30/60/90 días  
**Endpoint:** `GET /api/v1/radar` → retorna risk_scenarios + projected_cashflow  
**Entrada:** transactions (12 meses), tax_history, client_behavior, market_signals  
**Salida:** JSON {risk_scenarios, projected_cashflow, anomaly_flags, recommended_actions}  
**HITL:** ⚠️ PARCIAL (si risk > crítico, requiere acción en Hermes)  
**Test:** Proyecta escenarios, verifica razonabilidad vs histórico  
**Cadencia:** Semanal (10 AM lunes)  
**Integración KB:** "¿He visto este cliente en riesgo antes?" → busca en KB, aplica histórico

#### Agent 4: Auditoría Sombra (Continuous Audit)
**Responsabilidad:** Auditoría técnica automatizada, PDF reporte con hallazgos  
**Endpoint:** `POST /api/v1/wizard/auditoria-sombra`  
**Entrada:** erp_journal_entries, tax_filings_draft, bank_reconciliation  
**Salida:** PDF + email a auditor@cliente.com + archivo en Supabase  
**HITL:** ✅ SÍ (Entidad A firma como revisor fiscal, o rechaza)  
**Test:** Genera PDF con hallazgos (ej: "5 transacciones mal clasificadas")  
**Cadencia:** Mensual (cierre mes) o ad-hoc  
**Integración KB:** Hallazgos históricos → patrones → alerta si se repite  

**Hito 1 Checklist:**
- [ ] 4 agentes implementados
- [ ] 4 endpoints canónicos funcionales
- [ ] 4 services con lógica determinista
- [ ] 16 tests pass (4 × 4 test cases por agent)
- [ ] Cliente Cero valida cada agent
- [ ] Cada aprobación vectorizada → KB
- [ ] Hermes Workspace: menú para invocar 4 agentes
- [ ] Stage 11 reporte parcial (Agentes 1-4)

---

### HITO 2: Agentes Conversacional + Social — Semana 2

#### Agent 5: Taty (Conversational Operator + Telegram 24/7)
**Responsabilidad:** Interfaz conversacional: comandos naturales + Telegram bot  
**Endpoint:** `POST /api/v1/agents` (role: "taty") + Telegram webhook  
**Entrada:** Mensajes naturales ("¿cuánta caja hoy?" o "/ops conectar Stripe")  
**Salida:** Respuesta conversacional + links a acciones en Hermes  
**HITL:** ✅ SÍ (si usuario ejecuta comando sensible, Taty crea draft en Approval Queue)  
**Test:** Taty entiende 5 intenciones (status, pulso, radar, ideas, /ops)  
**Integración KB:** Usa KB para sugerir soluciones a excepciones ("he visto esto antes")  

#### Agent 6a: Content Idea Generator (Ideas → Drafts)
**Responsabilidad:** Ideas de contenido → borradores listos para publicar  
**Endpoint:** `GET /api/v1/social-ops/ideas` + `POST /ideas/{id}/generate-draft`  
**Entrada:** Idea raw (tema, pilar, formato)  
**Salida:** social_content_drafts (pending_approval)  
**HITL:** ✅ SÍ (marketing manager aprueba antes de publicar)  
**Test:** Draft valida tono vs SOUL.md  

#### Agent 6b: Lead Reply Drafter (CRM)
**Responsabilidad:** Respuestas a leads inbound (Telegram, Instagram, email)  
**Endpoint:** `POST /api/v1/social-ops/leads/reply-draft`  
**Entrada:** inbound_message + client_profile + conversation_history  
**Salida:** social_reply_drafts (pending_approval)  
**HITL:** ✅ SÍ (sales rep aprueba antes de enviar)  

#### Agent 6c: Sales Closure Drafter (Pipeline)
**Responsabilidad:** Propuestas de cierre personalizadas  
**Endpoint:** `POST /api/v1/social-ops/leads/sales-draft`  
**Entrada:** Lead hot, conversation history, pricing rules  
**Salida:** social_sales_drafts (pending_approval)  
**HITL:** ✅ SÍ (sales manager aprueba)  

#### Agent 6d: Metrics Analyzer (Pipeline Health)
**Responsabilidad:** Health de pipeline (leads by stage, conversion rate, churn)  
**Endpoint:** `GET /api/v1/social-ops/metrics`  
**Entrada:** social_leads, conversations, posts, campaign_metrics  
**Salida:** JSON {pipeline_by_stage, conversion_metrics, anomalies, recommendations}  
**HITL:** ❌ NO (solo lectura)  

**Hito 2 Checklist:**
- [ ] 6 agentes implementados (5 + 6a/6b/6c/6d)
- [ ] Taty entiende 5+ intenciones
- [ ] Social Ops migrado de n8n → FastAPI
- [ ] 20+ endpoints canónicos
- [ ] 28 tests pass (4 por agent × 7 agents)
- [ ] Hermes Workspace: menú para Taty + Social Ops
- [ ] Aprobaciones en Approval Queue (todas las acciones sensibles)

---

### HITO 3: Knowledge Base + Orchestrator — Semana 3

#### Agent 7: Knowledge Base (RAG + pgvector)
**Responsabilidad:** Base de conocimiento persistente, aprendizaje compuesto  
**Endpoint:** `GET /api/v1/kb` + RPC `match_knowledge_chunks()`  
**Entrada:** knowledge_chunks (vectores de decisiones aprobadas)  
**Salida:** Similar historical decisions + confidence scores  
**HITL:** ⚠️ PARCIAL (usa decisiones históricas, excepciones nuevas → HITL)  
**Integración:** Cada agente consulta KB antes de proponer acción inusual  

#### Agent 8: Maestro Orchestrator (Swarm Coordinator)
**Responsabilidad:** Orquestador central, paralleliza 5+ agentes  
**Endpoint:** `POST /hermes/swarm/invoke` o command `hermes orchestrator-maestro <action>`  
**Entrada:** Comando ("status", "nightly-audit", "approval-sync")  
**Salida:** JSON {agente1_result, agente2_result, ...} + síntesis narrativa  
**HITL:** ❌ NO (solo orquestación, HITL en agents)  
**Cadencia:** Manual (user-triggered) o Cron (2 AM nightly audit)  
**Performance:** < 500ms para parallelizar 5 agents  

**Hito 3 Checklist:**
- [ ] 8 agentes implementados
- [ ] Knowledge Base creciendo (vectoriza cada aprobación)
- [ ] Orchestrator paralleliza 5+ agents en < 500ms
- [ ] Fallback: si 1 agent falla, otros continúan
- [ ] Telemetría centralizada (cada acción logeada)
- [ ] Hermes Workspace: dashboard swarm status
- [ ] 40+ tests pass

---

### HITO 4: Hermes Workspace Integration — Semana 4

**Responsabilidad:** Dashboard React + menus + approval queue UI  
**Componentes:**
- [ ] Dashboard "Swarm Status" (5 agents in parallel, current results)
- [ ] "Approval Queue" (lista de pending_approval drafts, quick approve/reject)
- [ ] "Agents Panel" (invocar each agent, ver history, logs)
- [ ] "Knowledge Base Browser" (buscar decisiones históricas)
- [ ] "Metrics" (pipeline health, risk scores, forecasting)

**Hito 4 Checklist:**
- [ ] Hermes UI operativo (5+ pages)
- [ ] Real-time WebSocket para approval queue updates
- [ ] Integración con backend (todos los endpoints)
- [ ] Responsive design (web + mobile)
- [ ] Dark mode (SOUL.md)

---

### HITO 5: Stage 11 Deployment + Final Validation

**Responsabilidad:** Deploy a Railway, reporte final, validación Cliente Cero  
**Checklist:**
- [ ] Commit + push a main
- [ ] Railway rebuild (new deployment ID)
- [ ] /health endpoint = 200 OK
- [ ] E2E test (Cliente Cero) = PASS
- [ ] Stage 11 reporte completo (archivos, endpoints, tests, rollback)
- [ ] Telemetría verificada (logs de todas las acciones)
- [ ] Approval Queue funciona para TODOS los agentes
- [ ] Knowledge Base está creciendo (N decisiones vectorizadas)

---

## 🔐 MATRIZ HITL FINAL (para codificar)

| Agente | Acción | HITL | Gate | Notas |
|--------|--------|------|------|-------|
| Centinela | Generar asiento corrective | ✅ SÍ | Approval Queue | Entidad A aprueba |
| Pulso | Mostrar resumen diario | ❌ NO | — | Solo lectura |
| Radar | Alerta crítica (>90) | ⚠️ PARCIAL | Email + Hermes | Si crítico, requiere acción |
| Auditoría | Generar PDF reporte | ⚠️ PARCIAL | Email | Entidad A firma o rechaza |
| Taty | Ejecutar comando /ops | ✅ SÍ | Approval Queue | Comando sensible → draft |
| Content Ideas | Publicar contenido | ✅ SÍ | Approval Queue | Manager aprueba |
| Lead Reply | Enviar respuesta | ✅ SÍ | Approval Queue | Sales rep aprueba |
| Sales Draft | Enviar oferta | ✅ SÍ | Approval Queue | Sales manager aprueba |
| Metrics | Mostrar pipeline health | ❌ NO | — | Solo lectura |
| Orchestrator | Sincronizar todo | ❌ NO | — | Solo orquestación |

---

## 📊 MATRIZ DE DEPENDENCIAS (para arquitectura)

```
Orchestrator (8)
  ├─ Approval Queue (obligatorio para todos)
  │   ├─ Centinela (1)
  │   ├─ Social Ops (6a/6b/6c)
  │   ├─ Taty (when /ops)
  │   └─ Auditoría (4)
  │
  ├─ Pulso (2)
  │   ├─ Supabase transactions
  │   └─ KB (7) [busca explicaciones históricas]
  │
  ├─ Radar (3)
  │   ├─ pgvector embeddings
  │   ├─ LLM inference
  │   └─ KB (7)
  │
  ├─ Auditoría (4)
  │   ├─ Supabase RLS
  │   └─ PDF generator
  │
  ├─ Taty (5)
  │   ├─ Router to all agents
  │   ├─ LLM (Groq/Cerebras)
  │   └─ KB (7)
  │
  ├─ Social Ops (6)
  │   ├─ Ideas (6a) → Approval Queue
  │   ├─ Reply (6b) → Approval Queue
  │   ├─ Sales (6c) → Approval Queue
  │   ├─ Metrics (6d) → KB
  │   └─ Metrics analyzer
  │
  ├─ Knowledge Base (7)
  │   ├─ pgvector
  │   ├─ Embeddings service
  │   └─ Vectorización de decisiones aprobadas
  │
  └─ Approval Queue (obligatorio)
      └─ Triggers vectorización en 7 cuando draft es approved
```

---

## 🎯 PRE-REQUISITOS VERIFICAR ANTES DE EMPEZAR

```bash
# 1. pgvector habilitado
SELECT * FROM pg_extension WHERE extname='vector';
# Esperado: 1 row, version >= 0.8.0

# 2. knowledge_chunks table existe
SELECT COUNT(*) FROM knowledge_chunks;
# Esperado: tabla existe (puede estar vacía)

# 3. RPC match_knowledge_chunks callable
SELECT * FROM match_knowledge_chunks('[0.1, 0.2, ...]'::vector, 0.7, 5);
# Esperado: función existe

# 4. OPENAI_API_KEY en Railway
echo $OPENAI_API_KEY
# Esperado: key presente (no vacío)

# 5. Approval Queue endpoints existentes
curl https://antigravity-app-production-175a.up.railway.app/api/v1/approval-queue/
# Esperado: 200 OK o 404 (endpoint reconocido)

# 6. Cliente Cero data
SELECT COUNT(*) FROM [table_with_contexia_data];
# Esperado: datos reales para testing

# 7. Hermes Workspace URL
echo $HERMES_WORKSPACE_URL
# Esperado: https://hermes.contexia.online/ o similar
```

---

## 📚 ARCHIVOS CANÓNICOS A MANTENER SINCRONIZADOS

| Archivo | Propósito | Actualizar cuando |
|---------|-----------|-----------------|
| AGENTES.md | Catálogo de 9 agentes | Agregar agent, cambiar HITL rules |
| CLAUDE.md (proyecto) | Standards de código | Cambiar convenciones |
| openspec/config.yaml | Config de OpenSpec | Cambiar esquema de artifacts |
| ai-specs/openspec-deployment-standard/ | Stage 11 checklist | Actualizar criterios de "done" |
| openspec/changes/*/reports/*.md | Stage 11 deployment | Al terminar cada change |
| Hermes SOUL.md | Perfil/identidad | Cambiar UX/branding |

---

## 🚀 CHECKLIST FINAL (antes de llamar "FASE 4 completa")

- [ ] **9 Agentes implementados** (1 Centinela, 2 Pulso, 3 Radar, 4 Auditoría, 5 Taty, 6a/6b/6c/6d Social Ops, 7 KB, 8 Orchestrator)
- [ ] **9 Endpoints canónicos** (`GET/POST /api/v1/{centinela,pulso,radar,...}`)
- [ ] **HITL reglas codificadas** (qué requiere aprobación, qué no)
- [ ] **Approval Queue extendido** (todos los agentes integrados)
- [ ] **Knowledge Base creciendo** (decisiones aprobadas → vectorizadas)
- [ ] **Orchestrator sincroniza N agentes** en < 500ms
- [ ] **Cliente Cero valida cada agent** (datos reales de Contexia)
- [ ] **Hermes Workspace operativo** (menús, dashboards, approval queue UI)
- [ ] **60+ tests PASS** (6+ por agent × 9 agents, más E2E e integración)
- [ ] **Stage 11 Deployment** (commit + Railway rebuild + reporte)
- [ ] **Telemetría centralizada** (cada acción logeada con timestamp, operator, outcome)
- [ ] **Rollback plan documentado** (si 1 agent falla, qué ocurre)
- [ ] **Documentación actualizada** (AGENTES.md, CLAUDE.md, openspec/changes/*)

---

## 📖 REFERENCIAS CLAVE

| Documento | Ubicación | Propósito |
|-----------|-----------|-----------|
| Ground Truth v2.0 | Base-de-conocimientos-Contexia-v2.md | Identidad corporativa (Entidad B, Hermes Workspace) |
| APM Nominal | Nominal y Contexia_ Análisis Tecnológico.md | Modelo de 9 agentes (base) |
| AGENTES.md | AGENTES.md (este repo) | Catálogo completo, HITL rules, integración |
| CLAUDE.md | CLAUDE.md (proyecto) | Standards de código, OpenSpec rules |
| Stage 11 | DEPLOYMENT_STAGE/ | Checklist deployment obligatorio |
| FASE 3 Reporte | openspec/changes/add-pgvector-agent-critic-phase3/reports/ | Estado previo (base para FASE 4) |

---

## 💡 TIPS PARA EL AGENTE FASE 4

1. **No saltes pasos:** Agent por agent, baby steps, tests before code
2. **Cliente Cero primero:** Antes de proponer al mundo, testea con datos reales de Contexia
3. **HITL es ley:** Cualquier acción sensible → Approval Queue. Sin excepciones.
4. **Vectorización automática:** Cada aprobación → embedding → KB. Es el "secret sauce" de compounding memory.
5. **Documentación first:** AGENTES.md + OpenSpec specs antes de código. Documentación es source of truth.
6. **Stage 11 cada change:** No hay "casi listo". Commit + test + deploy + reporte. Siempre.
7. **Telemetría everywhere:** Cada acción debe tener timestamp, operator, outcome. Auditoría es garantía.
8. **Fallback graceful:** Si 1 agent falla, otros 8 continúan. Diseña para resiliencia.

---

**Documento mantenido por:** Dirección Contexia  
**Última actualización:** 2026-06-21  
**Próxima fase:** FASE 4 — Agentes 1-8 + Orchestrator  
**Estado:** Listo para iniciar nuevo chat
