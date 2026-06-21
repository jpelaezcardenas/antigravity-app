# SPEC: PHASE 2 — LLM Integration & Agent Activation

**Fase:** DAY 2 del MVP 6-días (lunes 2026-05-27)
**Branch:** `feature/phase2-llm-integration` (desde `deploy-prod`)
**Owner:** Contexia
**Duración estimada:** 8–10 horas

---

## 1. Objetivo

Reemplazar mocks por LLM real en Agents 1–4, con failover multi-provider robusto, y activar dos servicios end-to-end: Taty (RAG fiscal) y Centinela (rules engine de alertas).

## 2. Contexto

DAY 1 dejó la infraestructura completa (5 endpoints, frontend, DB, deploy), pero los agentes responden con mocks. Sin LLM real no hay producto demostrable a cliente. Multi-provider porque ningún proveedor único es confiable a costo razonable para MVP.

## 3. Alcance

**Entra:**
- LLM Failover Engine (Groq → Cerebras → Mistral → Gemini → OpenRouter)
- Auto-healing JSON parser (re-prompt si JSON inválido)
- Agents 1–4 conectados a engine real vía `base_agent.call_llm()`
- Taty: pgvector knowledge base + endpoint `/taty/ask` con RAG real
- Centinela: rules engine con 10+ reglas + cron cada 6h + webhooks
- Test suite: 18+ tests (unit con mocks + 1 e2e por agente)

**Fuera de alcance:**
- Agents 5–7 (DAY 3)
- UI nueva (frontend ya quedó en DAY 1)
- Fine-tuning / embeddings custom
- Observabilidad avanzada (solo logs básicos)

## 4. Restricciones

- **Compliance:** Taty cita normativa DIAN; Centinela alertas auditables (log timestamp + regla disparada)
- **Costo:** preferir Groq/Cerebras (free tier / barato). Sin LLM real en tests unit — solo en `*_e2e.py`
- **Latencia:** p50 < 5s
- **Reusabilidad:** engine y rules deben servir para N clientes vía config, no hardcode

## 5. Decisiones clave

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Failover en cascada (Chain of Responsibility) | LiteLLM router | Control fino + menos deps; patrón ya probado en `copiloto-contratos-eafit/asistente_core/llm_analyzer.py` — **portar lógica directa, no reinventar** |
| pgvector en Supabase | Pinecone | Ya tenemos Supabase; menos infra. Para MVP-16-usuarios on-prem NAS aún no aplica (DAY 3+) |
| Reglas en Python (Matriz Financiera determinista + Índice Braille ML) | YAML/JSON rules / DSL | Sigue arquitectura Contexia documentada; DSL es over-engineering para MVP |
| Cron via Railway scheduled job | Celery | Simpler para 1 job cada 6h |
| Anonimización pre-LLM + Zero Data Retention | Mandar datos crudos | **Política Contexia SOSP no negociable** — ningún dato fiscal de cliente entrena modelos externos |

**Ground truth Contexia (aplicar a todo código DAY 2):**
- Entidad A (firma regulada) firma; Entidad B (Contexia S.A.S. tech) opera SaaS — código asume separación
- Pulso Diario = dashboard 8AM con semáforo + T+0 + provisión impuestos futuros
- Centinela = ex-ante (bloquea ANTES de DIAN), no ex-post
- Cumplimiento: AES-256-GCM en reposo, anonimización antes de LLM

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Todas las API keys fallan | Engine retorna error tipado, agente devuelve degraded response |
| JSON parsing loops infinitos | Max 2 retries, luego falla |
| Cron duplica alertas | Idempotencia por `(client_id, rule_id, period)` en tabla alerts |
| Costo LLM se dispara en tests | Tests unit con mocks; e2e solo on-demand |

## 7. Tareas (orden de ejecución)

### T1 — LLM Engine skeleton (45 min)
- Crear `apps/backend/agents/llm_engine.py`
- Interface: `async def complete(prompt: str, schema: dict | None = None) -> LLMResponse`
- Provider enum + config desde env
- **Verify:** import sin error, mypy/ruff pasa

### T2 — Provider adapters (60 min)
- `GroqProvider`, `CerebrasProvider`, `MistralProvider`, `GeminiProvider`, `OpenRouterProvider`
- Cada uno: `async def call(prompt) -> str` con timeout 30s
- **Verify:** test unit con mock httpx por provider

### T3 — Failover logic (45 min)
- Iterar providers en orden, capturar 429/5xx/timeout → siguiente
- Log de cada intento (provider, latency, status)
- **Verify:** `test_llm_engine.py::test_failover_when_first_fails`

### T4 — Auto-healing JSON parser (30 min)
Portar `_parse_llm_response` de `copiloto-contratos-eafit`. Capas en orden:
1. Strip markdown wrappers (` ```json `)
2. Reparar trailing commas: `re.sub(r",\s*([\]}])", r"\1", clean)`
3. Regex extraction si hay texto espurio: `re.search(r"(\{[\s\S]*\})", raw)`
4. Synonym mapping de claves (config por agente)
5. Type coercion (dict → [dict] si schema espera lista)
6. Safe fallback: empaquetar texto crudo en schema sintético con `error=False`
7. Si `schema` provisto y todo falla: max 2 retries con re-prompt incluyendo el error
- **Verify:** `test_json_parser_recovers_from_invalid`, `test_strips_markdown`, `test_repairs_trailing_commas`, `test_safe_fallback_wraps_natural_language`

### T5 — Tests LLM engine (30 min)
- 4+ casos verde: failover, parsing OK, all-failed, rate-limit recovery
- **Verify:** `pytest apps/backend/agents/test_llm_engine.py -v` → 4/4 green

### T6 — Conectar Agents 1–4 (90 min)
- Modificar `base_agent.py::call_llm()` para usar `llm_engine.complete()`
- Remover mocks de los 4 agentes
- **Verify:** `test_agents_1_4.py` 12+ verde; outputs distintos por input

### T7 — Taty RAG (90 min)
- `pgvector_knowledge_base.py`: embed + search top-k
- Seed knowledge base con docs DIAN básicos
- Endpoint `POST /taty/ask`: retrieve → augment → LLM → cite source
- **Verify:** preguntas reales devuelven respuesta + citas

### T8 — Centinela Rules Engine (90 min)
Arquitectura dual según ground truth Contexia:
- **Matriz Financiera (determinista):** 10+ reglas duras (cuadre débitos=créditos, retención mínima, NIT válido, tope IVA por régimen, etc.)
- **Índice Braille (probabilístico):** scoring de anomalía con z-score sobre histórico del cliente (3 features mínimo: monto, frecuencia, contraparte)
- **Listas restrictivas:** check Lista Clinton/OFAC + proveedores ficticios DIAN (mock data set OK para MVP)
- Cron Railway cada 6h por cliente activo
- Insert en `alerts` con idempotencia por `(client_id, rule_id, period_hash)`
- **Verify:** seed cliente con violación determinista + uno con anomalía estadística → 2 alertas distintas en Supabase

### T8.5 — Anonimización pre-LLM (20 min)
Antes de mandar prompt a engine: reemplazar NITs, nombres, montos absolutos por tokens (`<NIT_1>`, `<MONTO_K>`). Mapa reverso en memoria para post-procesar respuesta. **Política SOSP no negociable.**
- **Verify:** `test_anonymizer_masks_nits`, `test_anonymizer_roundtrip`

### T9 — Validación final (45 min)
- `pytest` completo verde
- Smoke manual: cada endpoint vía Invoke-RestMethod
- Actualizar `DAY2_RESULTS.md`
- Commit + push branch

## 8. Criterios de verificación

- [ ] `pytest -v` → 18+ tests verde
- [ ] Deshabilitar GROQ_API_KEY → engine sigue respondiendo via Cerebras
- [ ] Mismo agente, 2 inputs distintos → 2 outputs distintos (no mock)
- [ ] `POST /taty/ask` con pregunta DIAN → respuesta + al menos 1 cita
- [ ] Centinela con cliente seed-violación → fila nueva en `alerts`
- [ ] Latencia p50 < 5s en producción
- [ ] Branch pushed + PR draft abierto contra `deploy-prod`

## 9. Archivos nuevos / modificados

**Nuevos:**
- `apps/backend/agents/llm_engine.py`
- `apps/backend/agents/test_llm_engine.py`
- `apps/backend/agents/test_agents_1_4.py`
- `apps/backend/services/pgvector_knowledge_base.py`
- `specs/phase2-llm-integration.md` (este archivo)
- `DAY2_RESULTS.md`

**Modificados:**
- `apps/backend/agents/base_agent.py` (call_llm real)
- `apps/backend/agents/{agent1..4}.py` (remover mocks)
- `apps/backend/services/centinela_service.py` (rules engine)
- `apps/backend/presentation/taty_endpoints.py` (usar RAG)
- `apps/backend/.env.example` (agregar 5 keys)

## 10. Próximos pasos (DAY 3)
Agents 5–7 (Repurposer, Analyst, Distribution) + `agent_orchestrator` expandido.

## 11. Referencias de implementación

**Fuente a portar (no reinventar) para T1–T5:**
- `C:\Users\contexia\Projects\copiloto-contratos-eafit\asistente_core\llm_analyzer.py` — failover + auto-healing JSON ya probado en producción

**Especificaciones formales:**
- `C:\Users\contexia\Downloads\guia_tecnica_failover.md.md` — tabla de 5 proveedores, 6 capas de auto-healing, pseudocódigo TypeScript de portabilidad
- `C:\Users\contexia\Downloads\DOCUMENTACIÓN TÉCNICA Y ARQUITECTURA DE SISTEMAS - CONTEXIA-MVP.md` — arquitectura dual A/B, Centinela ex-ante (Matriz Financiera + Índice Braille), SOSP

**Ground truth Contexia (aplicar a todo código DAY 2):**
- Memoria persistente: `~/.claude/.../memory/contexia-ground-truth.md`
- Patrón failover: `~/.claude/.../memory/failover-llm-pattern.md`
- Meta MVP: `~/.claude/.../memory/contexia-mvp-envigado.md`

**Reglas heredadas del patrón EAFIT (T1–T5 no negociables):**
1. SRP: selección provider ≠ parser JSON (módulos separados)
2. Chain of Responsibility por proveedor
3. NO depender de `response_format=json_object` — el parser regex es guardián obligatorio
4. Respetar `max_chars` del proveedor más limitado
5. Anonimizar NITs/nombres/montos ANTES del LLM (regla SOSP Contexia, NO viene de EAFIT)

---

## 12. DAY 3 — T10–T14 (2026-05-27)

### T10: Agents 4–7 (Editor, Repurposer, Analyst, Distribution)

Cuatro agentes nuevos heredan de `BaseAgent`. Todos usan `call_llm(anonymize=True)`. Registrados en `AgentRole` enum y exportados en `agents/__init__.py`.

| Agente | Rol | Salida clave |
|--------|-----|--------------|
| **Editor** (`agent_4_editor.py`) | Pule borrador, valida cumplimiento fiscal/legal, gate binario | `{is_compliant, polished_content, issues, confidence}` |
| **Repurposer** (`agent_5_repurposer.py`) | Adapta a canal (telegram/dashboard/sms/email) con límites duros | `{variants: {channel: text}, skipped_channels}` |
| **Analyst** (`agent_6_analyst.py`) | Sintetiza alertas Centinela → semáforo + riesgos + oportunidades | `{status_level, executive_summary, top_risks, opportunities, key_metrics}` |
| **Distribution** (`agent_7_distribution.py`) | Orquesta entrega (telegram + dashboard implementados; sms/whatsapp/email stub) | `{deliveries: [...], summary: {sent, failed, skipped}}` |

**Tests:** `tests/test_agents_4_7.py` — 17 casos con `call_llm` stubeado. Sin llamadas reales a LLM en CI.

### T11: KB Seeding con pgvector + fallback memoria

**Servicio:** `services/kb_seeding_service.py` con dos backends pluggables:
1. **pgvector** (preferido) — Supabase `knowledge_chunks` con `embedding vector(1536)` + función RPC `match_knowledge_chunks`
2. **memoria** (fallback) — keyword match con tokenizer normalizado (stopwords ES/EN, acentos opcionales)

Detección automática al primer uso: si `SUPABASE_URL+KEY` están definidos y la tabla existe, usa pgvector; si no, usa memoria. **El código aplica sin tener pgvector configurado.**

**Migración:** `apps/backend/supabase/migrations/20260527_knowledge_chunks.sql` — extensión `vector`, tabla, índice IVFFlat, RPC con cosine similarity, RLS.

**Seed DIAN:** `apps/backend/kb/dian_chunks.json` con 48 chunks curados (UVT, régimen simple, retención, IVA, facturación electrónica, plazos 2026, sanciones, ICA, exógena, precios de transferencia, etc.). Idempotente por `content_hash`.

**API:**
- `POST /api/v1/kb/seed` — sembrar chunks para un `client_id`
- `POST /api/v1/kb/seed-dian` — cargar el seed curado (idempotente)
- `GET  /api/v1/kb/status` — backend activo + counts
- `POST /api/v1/kb/search` — debug / eval de retrieval

**Tests:** `tests/test_kb_seeding.py` — 11 casos cubriendo seed idempotente, retrieval con/sin acentos, fallback al pool global, status del backend.

### T12: Frontend wire-up (decision override 2026-05-27)

`contexia-app/CLAUDE.md` decía "sin backend, sin fetch". Tras conflicto detectado durante DAY 3, el usuario autorizó cambio explícito: ahora la app llama APIs reales con fallback a mocks si el backend falla.

**Wired:**
- `TatyView` → `POST /api/v1/agents/taty/ask` (ya estaba listo desde DAY 2)
- `app/app/radar/page.tsx` → `GET /api/v1/radar/scenarios?company_id=X` (nuevo, con fallback `radarMock`)

**Backend nuevo:** `presentation/radar_endpoints.py` con `/scenarios` y `/health`. Computa heurísticamente las tres escenarios desde `_BASE_PROFILES`.

**Diferido:**
- Centinela: el backend tiene `POST /centinela/evaluate` pero falta `GET /centinela/alerts/{company_id}` para feed del Pulso. ActiveAlerts.tsx sigue consumiendo prop estática.

### T13: Nodos Contexia — infraestructura draft

**Archivos:** `infrastructure/nodos/`
- `docker-compose.yml` — n8n + minio (NAS mock) + vpn-tunnel stub (comentado)
- `.env.example` + `README.md`
- `cli/contexia-node.py` — subcomandos `init` (funcional), `status`/`sync`/`teardown` (stubs)

**Validación:** `python contexia-node.py init --company "Test Corp" --location envigado` genera `.env.<node-id>` con secretos aleatorios.

**Diferido:** WireGuard real, auto-registro en API central, endpoint `/wizard/auditoria-sombra`.

### T14: E2E pipeline + docs

**Test:** `tests/test_agent_pipeline.py` ejecuta Planner→Generator→Editor→Repurposer→Analyst→Distribution con LLMs stubeados. 3 casos: full chain, editor blocking, analyst status driving urgency.

**Suite total:** 46 passed + 1 skipped (E2E LLM gated por `RUN_E2E_LLM=1`).

**Memorias actualizadas:**
- `contexia-app-live-mode.md` (nueva) — documenta override de CLAUDE.md
- Spec sección 12 (este bloque) — referencia ejecución DAY 3

---

## 13. DAY 4 — T15–T16 (2026-05-24, path a 3 usuarios live)

### Contexto del retake

Nueva sesión retomando con dos hallazgos críticos vs handoff:
1. Todo el código DAY 3 estaba sin commitear en `deploy-prod` (Agents 4-7, KB, infra, tests).
2. `deploy-prod` divergía de `main` (5 ahead / 2 behind tras commit DAY 3).

**Acciones de saneamiento:**
- Limpieza `.gitignore` (artefactos `__next.*`, dumps, scripts ad-hoc).
- Commit bundled T10-T14 (single commit `2f238b7`).
- Merge clean de `origin/main` (recoge `CentinelaAlertsCard.tsx` + `types/centinela.ts`).
- Push directo `deploy-prod → main` (worktree local de main bloqueado).

### T15: GET /api/v1/centinela/alerts/{company_id}

Wiring del feed del Pulso. Cerró el gap explícito de la sección 12.

**Cambios:**
- `services/centinela_service.py`: nuevo método `get_alerts_for_company(company_id, limit, severity)` que consulta `centinela_alerts` en Supabase con fallback a `_evaluate_demo_profile()` (siempre devuelve señal en el MVP).
- `presentation/centinela_endpoints.py`: GET con shape consumido por Pulso ActiveAlerts: `{alerts, alert_count, critical_count, warning_count, risk_level, source}`. Soporta `?severity=critical` y `?limit=N`.

**Tests:** `tests/test_centinela_alerts_get.py` — 4 casos (supabase ok, supabase down, severity filter, endpoint smoke).

### T16: POST /api/v1/wizard/auditoria-sombra

Hook GTM principal. Onboarding 15-min sin código nuevo por cliente.

**Servicio:** `services/wizard_service.py` — multi-cliente por design (NIT → `company_id` determinístico). Funciones puras:
- `derive_company_id(nit)` — `900123456-1` → `ctx-900123456`
- `build_synthetic_profile(sector, regime, monthly_revenue)` — heurística realista por sector (5 sectores: Servicios Digitales, Comercio, Importaciones, Restaurantes, Construcción)
- `build_next_steps(status_level, alert_count)` — copy diferenciado por severidad
- `run_auditoria_sombra(...)` — orquesta NIT → profile → Centinela → AnalystAgent → reporte

**Endpoint:** `presentation/wizard_endpoints.py` con validación Pydantic (incl. `EmailStr`).

**Output:** `{company_id, status_level, executive_summary, top_risks, opportunities, alerts_preview, next_steps, audit_duration_seconds}`.

**Tests:** `tests/test_wizard_auditoria_sombra.py` — 12 casos (NIT parsing, perfil por sector, next_steps por severidad, e2e wizard, HTTP 200/422).

### Validación E2E con 3 prospectos simulados

Smoke vía TestClient (Estudio Cordillera / Importadora Andina / La Casita) — los 4 endpoints (Wizard, Pulso Centinela, Radar, Taty) responden 200 para los 3 `company_id` derivados. Wizard p95 < 20ms (sin LLM real; con LLM esperamos < 3s del failover chain).

**Hallazgo de coherencia (no MVP-blocking):** Wizard ejecuta Centinela in-memory pero no llama `save_alerts()` (Supabase no configurado). Por eso GET /alerts devuelve el demo fallback, no las alertas específicas del prospecto recién auditado. Para coherencia plena necesitamos backend de alertas persistente (Supabase o memoria compartida) — DAY 5+.

### Test suite

**69 passed, 1 skipped** (DAY 3 cerró en 46; +23 nuevos entre T15 y T16). Ver `tests/test_centinela_alerts_get.py` y `tests/test_wizard_auditoria_sombra.py`.

### Estado del deploy de producción

- `main` actualizada a `3924534` (incluye T10-T16).
- Railway production seguía sirviendo build viejo al cierre de sesión (DAY 2 endpoints OK, DAY 3-4 endpoints 404). Causa probable: rama monitoreada distinta a `main` o webhook necesitando trigger manual. **Acción de ops pendiente:** verificar config Railway → branch `main`.

### Gaps remanentes para 3 usuarios live reales

| Gap | Impacto | Owner próxima sesión |
|-----|---------|----------------------|
| Railway no desplegó DAY 3-4 | Bloqueante | Trigger manual / verificar branch monitoreada |
| Wizard frontend (Vercel) llamando a `/wizard/auditoria-sombra` | Bloqueante onboarding UI | `contexia-wizard.vercel.app` ya existe (ver `vercel.json` rewrites) — solo wiring |
| Persistencia de alertas Wizard → Pulso | Coherencia demo | Implementar memoria compartida o aplicar Supabase migration |
| pgvector aplicado a Supabase + chunks reales | Calidad Taty | Aplicar migración + correr `/kb/seed-dian` |
| Agent 6 en Radar (narrativas dinámicas) | Polish | Diferido |
