# PHASE 2: LLM Failover + Taty Fiscal + Centinela Rules
**Fecha:** Lunes 25 mayo 2026 (hoy domingo, mañana es sprinteable)  
**Rama:** `feature/phase2-llm-taty-centinela`  
**Release path:** Feature → Develop → Staging → Deploy-Prod

---

## 🎯 Objetivo
Entregar **3 capacidades nuevas sin romper lo existente:**
1. **LLM Failover Engine** - Groq → Cerebras → Mistral + auto-healing JSON + anonimización SOSP
2. **Taty Contadora** - Subagente fiscal orquestado, RAG mínimo DIAN, Telegram MVP
3. **Centinela Rules** - Motor de reglas fiscales, cálculos ex-ante, alertas en Supabase

---

## 📋 Alcance por Componente

### A. LLM Failover Engine (Backend)
**Estado:** Código existe en `apps/backend/agents/llm_engine.py` sin tests  
**Completar:**
- ✅ 5 providers (Groq, Cerebras, Mistral, Gemini, OpenRouter)
- ✅ Chain of Responsibility failover
- ✅ JSON auto-healing (trailing commas, type coercion, synonyms)
- ✅ Anonimizador SOSP (NIT, correo, teléfono, dinero → tokens antes de enviar)
- ❌ **Tests:** 8+ casos (failover, rate limits, all-failed, retry logic)
- ❌ **BaseAgent.call_llm()** - Integración en `base_agent.py`

**Criterio de éxito:**
- `pytest tests/test_llm_engine.py -v` → 18+ tests verdes
- Latencia P95 < 5s en Groq (cached)
- No hay API keys en logs/respuestas

---

### B. Taty Contadora (Backend + API + Dashboard)
**Arquitectura:** Subagente orquestado, NO independiente  
**Componentes:**

#### 1. Backend: TatyAgentService
**Archivo:** `apps/backend/services/taty_service.py` (nuevo)  
**Responsabilidades:**
- Recuperar `agent_profile` por `company_id` (config, tono, sector, restricciones)
- RAG minimal: cargar chunks de Normograma DIAN + documentos Contexia
- Generar prompt fiscal + contexto cliente
- Llamar LLM vía `llm_engine.get_ai_response()` con anonimización
- Retornar: respuesta + citas de fuentes + latencia + `requires_human_review`

**Interfaces:**
```python
POST /api/v1/agents/taty/ask
{
  "company_id": "nit-900-123-456-7",
  "question": "¿Cuál es el UVT 2026?",
  "channel": "telegram|dashboard|whatsapp",  # para estadísticas
  "conversation_id": "conv-uuid",
  "user_id": "user-uuid"
}

Response:
{
  "answer": "El UVT 2026 es $52.374...",
  "citations": [
    {"source": "Resolución DIAN 238/2025", "fragment": "..."}
  ],
  "latency_ms": 2340,
  "confidence": 0.92,
  "requires_human_review": False,
  "result": "answer"  # compatibilidad temporal
}
```

#### 2. Persistencia Mínima (Supabase)
**Tablas nuevas:**
- `agent_profiles` - config por cliente (NIT, tono, sector, fuentes habilitadas)
- `knowledge_sources` - metadatos de fuentes (DIAN, Estatuto, Contexia docs)
- `knowledge_chunks` - fragmentos versionados (source_id, texto, embedding?)
- `conversations` - historial por cliente+channel (company_id, channel, created_at)
- `conversation_messages` - mensajes (conversation_id, role, content, latency_ms, requires_human_review)

#### 3. Webhook Telegram (Backend)
**Archivo:** `apps/backend/presentation/telegram_endpoints.py` (nuevo)  
**Endpoint:** `POST /api/v1/channels/telegram/webhook`  
**Flujo:**
1. Recibe update de Telegram API (JSON)
2. Resuelve `company_id` (mapeo piloto: TELEGRAM_CHAT_ID → NIT)
3. Extrae pregunta (`message.text`)
4. Llama `TatyAgentService.ask()`
5. Responde vía Telegram Bot API (`sendMessage`)
6. Loguea conversación en `conversation_messages`

**Prerequisito:** `TELEGRAM_BOT_TOKEN` en `.env` (crear bot con BotFather)

#### 4. Dashboard Integration
**Archivo:** `Contexia_Daschboard/src/components/taty/TatyView.tsx` (actualizar)  
**Cambios:**
- Reemplazar `getResponse(keyword)` con llamada real: `api.askTaty(company_id, question)`
- Endpoint: `GET /api/v1/agents/taty/ask?company_id=...&question=...`
- Mostrar citations + latencia + badge "requires_human_review"
- Mantener UI existente (no rediseñar), solo conectar a API real

---

### C. Centinela Rules Engine (Backend)
**Archivo:** `apps/backend/services/centinela_service.py` (actualizar)  
**Scope para este MVP:**
- ✅ 10+ reglas básicas (cálculos de renta, retenciones, UVT, comparativas)
- ✅ Runner cron cada 6h (no implementar cron aún, solo servicio)
- ✅ Escribir alerts a `alerts` table en Supabase
- ❌ Webhooks de notificación (fase posterior)

**Reglas MVP:**
1. UVT base anual vs. cliente histórico
2. Retención por IVA vs. presupuesto
3. Patrimonio vs. límites Régimen Simple
4. Días sin movimiento → alerta liquidez
5. Facturación electrónica no registrada en DIAN
6. Crédito fiscal no arrastrado
7. Provisión contable vs. obligación fiscal
8. Cambio de régimen detectado
9. Índice Braille (patrimonio neto / activos)
10. Cobertura de reservas (caja / gastos mensuales)

**Output:** Tabla `alerts` con `(company_id, rule_id, severity, recommendation, created_at)`

---

## 📅 Timeline (Lunes 25 mayo)
| Tarea | Horas | Responsable | Status |
|-------|-------|-------------|--------|
| **T1** Setup rama + permisos | 0.5h | - | ⏳ |
| **T2** Tests llm_engine.py (8+) | 2h | - | ⏳ |
| **T3** Integrar BaseAgent.call_llm() | 1h | - | ⏳ |
| **T4** TatyAgentService + prompt fiscal | 2h | - | ⏳ |
| **T5** Schema Supabase (agent_profiles, chunks, etc.) | 1h | - | ⏳ |
| **T6** Telegram webhook + BotFather setup | 1.5h | - | ⏳ |
| **T7** Dashboard TatyView + API real | 1h | - | ⏳ |
| **T8** Centinela 10 reglas + alertas | 2h | - | ⏳ |
| **T9** Validación end-to-end (API, Telegram, Dashboard) | 1h | - | ⏳ |
| **T10** Push a develop + PR | 0.5h | - | ⏳ |
| **Buffer** (inesperados) | 1h | - | ⏳ |
| **TOTAL** | **13.5h** | | |

**Estrategia:** 
- ✅ Hoy (domingo): Spec + plan
- ✅ Mañana 08:00–14:00: Core (T1–T5)
- ✅ Mañana 14:00–18:30: Integraciones (T6–T9)
- ✅ Mañana 18:30–19:00: Push + PR (T10)

---

## ⚠️ Riesgos & Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|-----------|
| No hay TELEGRAM_BOT_TOKEN | Alta | Bloqueador | Crear bot con BotFather antes de T6; fallback: guardar endpoint listo |
| LLM providers offline | Media | T2 bloqueado | Usar mocks en tests; providers pueden caer en producción (fallover absorbe) |
| Schema Supabase migration falla | Baja | T5 bloqueado | Test migration en staging primero; rollback script |
| Tiempo insuficiente | Media | Calidad baja | Priorizar: T2+T4+T9 (core funcional); T8 puede ser reglas mínimas (5 en vez de 10) |
| Contrato de respuesta cambia | Baja | Usuarios dashboard | Mantener `result` como alias de `answer`; validar en T9 |

---

## ✅ Criterios de Éxito

### A. LLM Engine
- [ ] `pytest tests/test_llm_engine.py -v` → 18+ verde
- [ ] Latencia P95 < 5s (Groq cached)
- [ ] Failover en acción: Groq 429 → Cerebras ok
- [ ] No hay API keys en logs

### B. Taty
- [ ] API `POST /api/v1/agents/taty/ask` responde en < 4s
- [ ] Respuesta incluye citas (source + fragment)
- [ ] Dashboard TatyView usa API real (no mocks)
- [ ] Telegram webhook recibe + responde msg real
- [ ] Conversaciones loguadas en Supabase

### C. Centinela
- [ ] 10+ reglas definidas en código
- [ ] `CentinelaService.check_rules(company_id)` retorna alerts[]
- [ ] Alerts se escriben a tabla Supabase

### D. Sin Romper Existente
- [ ] Pulso 200 OK
- [ ] Cobro endpoints vivos
- [ ] Social Ops agents sin cambio
- [ ] Auth/CRM sin regresiones

---

## 📚 Recursos Locales
- **LLM Engine:** `apps/backend/agents/llm_engine.py` (ya existe, falta tests)
- **Anonymizer:** `apps/backend/agents/anonymizer.py` (SOSP integrado)
- **Tests:** `apps/backend/tests/test_llm_engine.py` (template existe)
- **Config fiscal:** `apps/backend/config.py` (UVT, retención rates)
- **Spec original:** `specs/phase2-llm-integration.md` (referencia)
- **Contexia Ground Truth:** `~/.claude/memory/contexia-ground-truth.md` (SOSP, dual A/B, arquitectura)

---

## 🚀 Post-MVP (No en esta sesión)
- WhatsApp + integración n8n
- IA para generar respuestas (LLM generativo en lugar de RAG puro)
- Embedding + búsqueda vectorial real (pgvector)
- Análisis de sentimiento + escalamiento automático humano
- Taty por cliente (personalización por sector, NIT)
- Estadísticas de confianza y feedback loop

---

**Próximo paso:** Confirma si procedo con T1 (setup) o si necesitas ajustes en el plan.
