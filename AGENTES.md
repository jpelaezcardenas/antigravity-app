# 📋 AGENTES DE CONTEXIA — Catálogo Completo (v2.0)

**Ubicación en repo:** antigravity-app/AGENTES.md + ai-specs/agents/AGENTES.md (symlink)  
**Versión:** 2.0 | **Fecha:** 2026-06-21  
**Propietario:** Dirección Contexia  
**Alineación:** Ground Truth v2.0 + APM Nominal + Hermes Workspace + Cliente Cero

---

## 🎯 Propósito de este documento

Este catálogo define la topología completa de **9 agentes** que orquesta **Hermes Workspace** en Contexia. Cada agente es especializado, determinista, responde a un endpoint canónico (`/api/v1/*`), y se alinea con el modelo **Agentic Performance Management (APM)** de Nominal adaptado al contexto fiscal-contable-comercial colombiano.

### Principios arquitectónicos:
- ✅ **Spec-first**: Documentación es fuente de verdad
- ✅ **Determinismo**: AgentCritic valida antes de proponer (no alucinaciones)
- ✅ **HITL obligatorio**: Approval Queue = gate para acciones sensibles
- ✅ **Cliente Cero**: Contexia es primer cliente productivo antes de externos
- ✅ **Preservación de Marketing**: Content OS + Social Ops se integran sin perder capacidades

---

## 📂 Taxonomía de agentes

```
CONTEXIA SWARM (Hermes Workspace)
│
├─ TIER 1: CORE FISCAL-CONTABLE (modelo APM Nominal)
│  ├─ Centinela Fiscal (1) — Transaction Patrol + Resolution
│  ├─ Pulso Diario (2) — Flux Analysis
│  ├─ Radar Predictivo (3) — Pattern Recognition + Forecasting
│  └─ Auditoría Sombra (4) — Continuous Audit
│
├─ TIER 2: CONVERSACIONAL & ONBOARDING
│  └─ Taty (5) — Conversational Operator + 24/7
│
├─ TIER 3: SOCIAL OPS & MARKETING (Content OS heredado)
│  ├─ Content Idea Generator (6a) — Ideas → Drafts
│  ├─ Lead Reply Drafter (6b) — CRM Responses
│  ├─ Sales Closure Drafter (6c) — Pipeline Closures
│  └─ Metrics Analyzer (6d) — Pipeline Health
│
├─ TIER 4: KB & RETRIEVAL
│  └─ Knowledge Base (7) — RAG + pgvector
│
├─ TIER 5: ORQUESTACIÓN
│  └─ Maestro Orchestrator (8) — Swarm Coordinator
│
└─ TIER 6: HITL (obligatorio para todos)
   └─ Approval Queue (9) — Central Human-in-the-Loop Gate
```

---

## 🔧 AGENTES DETALLADOS

### TIER 1: CORE FISCAL-CONTABLE

#### 1. CENTINELA FISCAL (Transaction Patrol + Resolution Agents)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET/POST /api/v1/centinela` |
| **Tipo** | Transaction Patrol (auditoría continua) + Resolution (generador de drafts) |
| **Función canónica** | Monitorea DIAN, vencimientos, discrepancias contables en tiempo real |
| **Modelo Nominal** | Transaction Patrol Agent — Detecta anomalías; Resolution Agent — Genera asientos correctivos |
| **Entrada** | `dian_xml_documents` (facturas DIAN) + `erp_journal_lines` (contabilidad interna) |
| **Proceso** | 1. Compara semánticamente DIAN vs ERP. 2. Detecta discrepancias (monto, fecha, NIT). 3. Genera payload JSON. 4. Enqueue en Approval Queue. |
| **Salida** | `tax_correction_drafts` (pending_approval) |
| **HITL** | ✅ SÍ — Entidad A aprueba/rechaza ajustes contables |
| **Dependencias** | contexia-shared, Approval Queue, Siigo API, DIAN webhook |
| **Cliente Cero** | ✅ Testea con datos tributarios reales de Contexia |
| **Cadencia** | Continua (no mes-end batch) |

**Casos de uso:**
- Factura DIAN $10M sin asiento contable en Siigo → genera ajuste
- Retención en la fuente no reportada → detecta y propone corrección
- Variación de tasa de cambio en transacción interpañía → calcula reclasificación

---

#### 2. PULSO DIARIO (Flux Analysis Agent)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/pulso` |
| **Tipo** | Flux Analysis Agent — Genera narrativas explicativas de variaciones |
| **Función canónica** | Estado operativo/fiscal diario: resumen automatizado de alertas, vencimientos, caja, señales |
| **Entrada** | `transactions` (últimas 24h), `tax_alerts` (vencimientos), `bank_feeds` (saldos de caja) |
| **Salida** | JSON: `{caja_disponible, vencimientos_hoy, variaciones_detectadas, narrative_summary}` |
| **HITL** | ❌ NO — Solo lectura; Entidad A revisa, no aprueba |
| **Cadencia** | Diaria (9 AM; cron: `0 9 * * 1-5`) |

---

#### 3. RADAR PREDICTIVO (Pattern Recognition + Forecasting)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/radar` |
| **Tipo** | Predictive Risk Analysis + Pattern Recognition |
| **Función canónica** | Análisis predictivo: anticipa riesgos fiscales, de negocio, cashflow stress |
| **Entrada** | `transactions` (12 meses), `tax_history`, `client_behavior`, `market_signals` |
| **Salida** | JSON: `{risk_scenarios, projected_cashflow, anomaly_flags, recommended_actions}` |
| **HITL** | ⚠️ PARCIAL — Hermes muestra alertas; si riesgo crítico, Entidad A decide acción |
| **Cadencia** | Semanal (cron: `0 10 * * 1`) |

---

#### 4. AUDITORÍA SOMBRA (Continuous Audit Agent)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /api/v1/wizard/auditoria-sombra` |
| **Tipo** | Continuous Audit (no reemplaza revisoría fiscal legal) |
| **Función canónica** | Revisión técnica automatizada: emite reportes PDF de hallazgos contables/fiscales |
| **Entrada** | `erp_journal_entries`, `tax_filings_draft`, `bank_reconciliation` |
| **Salida** | PDF report + email a auditor@cliente.com + archivo en Supabase |
| **HITL** | ✅ SÍ — Entidad A revisa, valida, firma como revisor fiscal (o declara que no firma) |
| **Cadencia** | Mensual (cierre mes) o ad-hoc |

---

### TIER 2: CONVERSACIONAL

#### 5. TATY (Conversational Operator + Telegram 24/7)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /api/v1/agents` (role: `"taty"`) + Telegram webhook |
| **Tipo** | Conversational + Zero-UI Command Parser |
| **Función canónica** | Operador 24/7: fiscal conversacional, soporte Telegram, onboarding, comandos Social Ops |
| **Entrada** | Mensajes naturales (chat, Telegram, Slack, email) |
| **Proceso** | 1. Parse intención. 2. Invoca skill correspondiente. 3. Retorna respuesta natural + links a acciones en Hermes |
| **Salida** | Respuesta conversacional + oferta de acciones |
| **HITL** | ✅ SÍ — Si comando sensible, Taty lo dirige a Approval Queue |
| **Cadencia** | Continua (24/7) |
| **Cliente Cero** | ✅ Público en Telegram de Contexia (@contexia_bot) |

**Casos de uso:**
- "¿Cuánta caja tengo hoy?" → Taty consulta Pulso
- "/ops conectar Stripe" → Taty crea draft en Approval Queue
- "¿Qué clientes son de riesgo?" → Taty consulta Radar, enumera top 5

---

### TIER 3: SOCIAL OPS & MARKETING

#### 6a. Content Idea Generator (Ideas → Drafts)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/social-ops/ideas` + `POST /ideas/{id}/generate-draft` |
| **Tipo** | Content Brainstormer (LLM-guided) + Draft Generator |
| **Función** | Genera ideas de contenido, convierte en borrador listo para publicar |
| **HITL** | ✅ SÍ — Entidad A aprueba publicación |

#### 6b. Lead Reply Drafter (CRM)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /api/v1/social-ops/leads/reply-draft` |
| **Tipo** | Conversational Reply Generator |
| **Función** | Genera respuestas a leads inbound (Telegram, Instagram, email) |
| **HITL** | ✅ SÍ — Sales rep aprueba antes de enviar |

#### 6c. Sales Closure Drafter (Pipeline)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /api/v1/social-ops/leads/sales-draft` |
| **Tipo** | Sales Strategy + Offer Generator |
| **Función** | Genera propuestas de cierre personalizadas |
| **HITL** | ✅ SÍ — Sales manager aprueba |

#### 6d. Metrics Analyzer (Pipeline Health)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/social-ops/metrics` |
| **Tipo** | Flux Analysis (para marketing, no finanzas) |
| **Función** | Analiza health de pipeline: leads by stage, conversion rate, churn |
| **HITL** | ❌ NO — Solo lectura |

---

### TIER 4: KNOWLEDGE BASE

#### 7. Knowledge Base (RAG + pgvector)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/kb` + RPC `match_knowledge_chunks()` |
| **Tipo** | Retrieval-Augmented Generation (RAG) |
| **Función canónica** | Base de conocimiento persistente: decisiones históricas + soluciones + políticas |
| **Entrada** | `knowledge_chunks` (pgvector embeddings) |
| **Salida** | Similar historical decisions + context |
| **HITL** | ⚠️ PARCIAL — Usa decisiones aprobadas; para nuevas excepciones, requiere HITL |
| **Cadencia** | Continua (aprendizaje acumulativo) |

---

### TIER 5: ORQUESTACIÓN

#### 8. Maestro Orchestrator (Swarm Coordinator)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /hermes/swarm/invoke` o `hermes orchestrator-maestro <action>` |
| **Tipo** | Meta-agent (coordina otros 8 agentes) |
| **Función canónica** | Delega a 5+ subagentes en paralelo, sintetiza resultados |
| **Entrada** | Comando natural ("status", "nightly-audit", "approval-sync") |
| **Proceso** | 1. Parse acción. 2. Delega a N subagentes en paralelo. 3. Espera resultados. 4. Sintetiza narrativa. |
| **Salida** | JSON con resultados + síntesis narrativa |
| **HITL** | ❌ NO — Solo orquestación (HITL ocurre en Approval Queue) |
| **Performance** | < 500ms para parallelizar 5 agents |

---

### TIER 6: HITL (obligatorio)

#### 9. Approval Queue (Central Gate)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/approval-queue` + `POST /approvals/{id}/approve\|reject` |
| **Tipo** | Task Management + Human-in-the-Loop Gate |
| **Función canónica** | Gate HITL obligatorio: nada outbound se ejecuta sin aprobación explícita |
| **Draft types** | `command`, `reply_draft`, `sales_draft`, `tax_correction` |
| **HITL** | ✅ SÍ — Obligatorio |

---

## 🔐 Matriz HITL (Human-in-the-Loop)

| Agente | Acción | HITL | Gate | Notas |
|--------|--------|------|------|-------|
| Centinela | Generar asiento corrective | ✅ SÍ | Approval Queue | Entidad A aprueba ajuste contable |
| Pulso | Mostrar resumen diario | ❌ NO | — | Solo lectura |
| Radar | Alerta de riesgo crítico | ⚠️ PARCIAL | Email + Hermes | Si score > 90, requiere acción |
| Auditoría Sombra | Generar PDF reporte | ⚠️ PARCIAL | Email | Entidad A firma o rechaza |
| Taty | Ejecutar comando /ops | ✅ SÍ | Approval Queue | Comando sensible → draft |
| Content Ideas | Publicar contenido | ✅ SÍ | Approval Queue | Manager aprueba |
| Lead Reply | Enviar respuesta | ✅ SÍ | Approval Queue | Sales rep aprueba |
| Sales Draft | Enviar oferta | ✅ SÍ | Approval Queue | Sales manager aprueba |
| Metrics | Mostrar pipeline health | ❌ NO | — | Solo lectura |
| Orchestrator | Sincronizar todo | ❌ NO | — | Solo orquestación |

---

## 🏭 Mapeo a Modelo APM Nominal

| Agente Contexia | Agente Nominal | Similitud | Diferencia |
|-----------------|----------------|-----------|-----------|
| Centinela Fiscal | Transaction Patrol + Resolution | 100% | Adaptado a fiscalidad colombiana (DIAN, Siigo) |
| Pulso Diario | Flux Analysis Agent | 95% | Enfocado en estado operativo diario |
| Radar Predictivo | Pattern Recognition + Forecasting | 80% | Nominal no tiene forecasting explícito |
| Auditoría Sombra | Continuous Audit (conceptual) | 70% | Contexia expone auditoría como agente público |
| Taty | N/A (Nominal = monolítico) | — | Conversational interface nueva |
| Social Ops | N/A (fuera de APM Nominal) | — | Heredado de Content OS |
| Knowledge Base | Compounding Memory (pgvector) | 100% | Vectorizar decisiones para reutilizar |

---

## 🎯 Reglas Operativas

**Regla 1: HITL Obligatorio en Sensible**
- ✅ Estados financieros (asientos contables)
- ✅ Comunicación outbound (replies, ventas, publicaciones)
- ✅ Cambios de configuración crítica (/ops)
- ✅ Datos tributarios (declaraciones)

**Regla 2: Cliente Cero Antes de Externos**
- Testear con datos reales de Contexia
- Documentar evidencia en Stage 11 reporte
- Entidad A valida antes de ir a producción

**Regla 3: Determinismo Antes de IA**
- Centinela: lógica determinista (comparación DIAN vs ERP)
- Auditoría: validación aritmética exacta
- Social Ops: LLM guía draft, pero Entidad A decide

**Regla 4: No Volver a n8n Legacy**
- Toda lógica social-ops = en FastAPI canónico
- Si se reutiliza workflow n8n, documentar como auxiliar

**Regla 5: Preservación de Marketing/Ventas**
- Ideas → Drafts → Metrics pipeline = preservado
- Lead scoring + reply generation = preservado
- Todo pasa por HITL (Approval Queue)

---

## 📍 Ubicación de Artefactos

```
antigravity-app/
├── AGENTES.md ← Este documento
├── ai-specs/agents/
│   └── AGENTES.md (symlink o copia)
├── apps/backend/presentation/
│   ├── centinela_endpoints.py
│   ├── pulso_endpoints.py
│   ├── radar_endpoints.py
│   ├── audit_endpoints.py
│   ├── taty_endpoints.py
│   ├── social_ops_endpoints.py
│   ├── kb_endpoints.py
│   ├── orchestrator_endpoints.py
│   └── approval_queue_endpoints.py
├── apps/backend/services/
│   ├── centinela_service.py
│   ├── pulso_service.py
│   ├── radar_service.py
│   ├── audit_service.py
│   ├── taty_service.py
│   ├── social_ops_service.py
│   ├── kb_service.py
│   └── orchestrator_service.py
└── openspec/
    └── changes/hermes-swarm-contexia/
        └── Stage 11 artifacts
```

---

**Documento mantenido por:** Dirección Contexia  
**Última actualización:** 2026-06-21  
**Estado:** Ready for FASE 4 implementation  
**Próxima fase:** Agent implementation + Hermes Workspace orchestration
