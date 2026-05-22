# LLM Audit - Contexia Backend

**Fecha:** 2026-05-22  
**Estado:** T1 - Auditoría Inicial  
**Objetivo:** Mapear todas las tareas LLM actuales y propuestas, asignar tiers de modelo

---

## ESTADO ACTUAL

### Código Base
- ✅ `agents/llm_engine.py` EXISTE con 5 providers: Groq, Cerebras, Mistral, Gemini, OpenRouter
- ❌ LLMEngine NO está integrado en app actual (main.py, endpoints)
- ❌ Endpoints de agentes NO existen aún (router.py menciona `llm_endpoints`, `agents_endpoints` pero no están creados)
- ✅ Servicios existentes: PulsoService, CentinelaService, AlertasService (sin LLM)

---

## TAREAS IDENTIFICADAS & MAPEO A TIERS

### Matriz: Tarea → Costo Actual → Tier Propuesto → Modelo Seleccionado

| Tarea | Descripción | Costo Actual | Frecuencia | Sensibilidad | Tier | Modelo | Razón |
|-------|-------------|-------------|-----------|-------------|------|--------|-------|
| **Pulso Analysis** | Análisis diario de transacciones, "dinero tuyo hoy" | Groq $0.15/llamada | 1x/día/usuario | Alto (datos financieros) | TIER 2 | **Ollama Local** | Datos privados, no salen del servidor, análisis simple |
| **Centinela Monitoring** | Evaluación de umbrales fiscales (Renta, IVA) | Groq $0.15/llamada | 1x/día/usuario | Alto (datos financieros) | TIER 2 | **Ollama Local** | Datos financieros críticos, requiere privacidad, cálculos locales |
| **Centinela Decision** | Recomendación fiscal crítica (¿Declarar? ¿IVA?) | Groq $0.20/llamada | Bajo, on-demand | Crítico (fiscal/DIAN) | TIER 3 | **Groq** | Decisión fiscal → responsabilidad legal, requiere modelo confiable |
| **Taty FAQ Lookup** | Responder FAQ sobre impuestos, facturación, proceso | Openrouter Free | 10x/día/usuario | Bajo (FAQ pública) | TIER 1 | **OpenRouter Free** | Datos no-sensibles, búsqueda simple, sin instalación |
| **Data Extraction** | Extraer datos de documentos, facturas, recibos | Gemini $0.05/llamada | 5x/día/usuario | Medio (OCR general) | TIER 1 | **OpenRouter Free** | Tarea simple, modelos open-source suficientes |
| **Social Media Content Gen** | Generar posts, captions para redes | Gemini $0.05/llamada | 10x/día | Bajo (marketing) | TIER 1 | **OpenRouter Free** | Creatividad no-crítica, OpenRouter maneja bien |
| **Compliance Audit** | Revisar cumplimiento DIAN, retenciones | Groq $0.20/llamada | Bajo, on-demand | Crítico (regulatorio) | TIER 3 | **Groq** | Decisión legal/compliance, no negociable |
| **Social Media Analysis** | Analizar sentimiento, performance de posts | Gemini $0.05/llamada | 1x/día | Bajo | TIER 1 | **OpenRouter Free** | Análisis básico, modelos open-source suficientes |

---

## COSTOS ACTUALES (Estimado)

### Por Proveedor
- **Groq** (Pulso, Centinela, Compliance): ~$50-80/mes
- **Gemini** (Data extraction, Social): ~$20-40/mes
- **OpenRouter** (fallback): ~$5-10/mes
- **Cerebras, Mistral** (raros): <$5/mes

**Total actual:** ~$100-150/mes en APIs (para ~1-2 usuarios activos)

### A Escala (5 clientes activos)
- **Groq:** ~$250-400/mes
- **Gemini:** ~$100-200/mes
- **Total:** ~$400-600/mes

**NOTA:** El plan initial asumía $3.000/mes, pero en realidad es ~$400-600/mes. La auditoría revela que los costos son MENORES de lo previsto. La optimización sigue siendo valiosa (reducir a ~$100-150/mes).

---

## TIER ASSIGNMENT SUMMARY

### TIER 1: OpenRouter Free (NO-SENSIBLE, SIMPLE)
**Modelos:** Mistral, Llama, Qwen  
**Modelos Gratis:** SÍ (~100 req/día libre)  
**Tareas:**
- Taty FAQ Lookup
- Data Extraction (OCR simple)
- Social Media Content Gen
- Social Media Analysis

**Beneficio:** Gratis, sin instalación, infraestructura delegada

---

### TIER 2: Ollama Local (FINANCIERO, PRIVADO)
**Modelos:** DeepSeek V4, Mistral 7B (instalados en Railway)  
**Instalación:** One-time (2h), Railway server  
**Tareas:**
- Pulso Analysis
- Centinela Monitoring

**Beneficio:** Máxima privacidad, datos nunca salen del servidor, reducción de latencia

**Fallback:** Si Ollama timeout >2s → OpenRouter Free automático (no bloquear usuario)

---

### TIER 3: Groq (CRÍTICO, FISCAL/COMPLIANCE)
**Costo:** $0.20/llamada aprox  
**Tareas:**
- Centinela Decision (fiscal crítica)
- Compliance Audit (regulatorio)

**Beneficio:** Modelo garantizado, responsabilidad legal clara

---

## IMPLEMENTACIÓN: PLAN DE INTEGRACIÓN

### Paso 1: Extender LLMEngine (apps/backend/agents/llm_engine.py)
**Agregar proveedores:**
```python
class LLMProvider(Enum):
    GROQ = "groq"
    CEREBRAS = "cerebras"
    MISTRAL = "mistral"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OPENROUTER_FREE = "openrouter_free"  # ← NUEVO
    OLLAMA = "ollama"                     # ← NUEVO
```

**Agregar métodos:**
- `_call_openrouter_free()` - Llamadas OpenRouter Free (sin autenticación específica, o clave pública)
- `_call_ollama()` - Llamadas locales a Ollama (http://localhost:11434)

**Modificar failover:**
```python
def get_ai_response(...) -> Union[Dict, str]:
    provider_order = [
        LLMProvider.OLLAMA,         # Intenta local primero (si es Tier 2)
        LLMProvider.OPENROUTER_FREE, # Si no es Tier 2 o falla, intenta free
        LLMProvider.GROQ,           # Si ambas fallan, Groq (pago)
    ]
```

---

### Paso 2: Crear Model Selector (NEW: apps/backend/core/model_selector.py)
```python
def choose_model_for_task(task_type: str) -> LLMProvider:
    """
    Decide automáticamente qué modelo usar basado en sensibilidad de datos
    """
    
    # TIER 1: OpenRouter Free
    if task_type in [
        "taty_faq",
        "data_extraction",
        "social_content_gen",
        "social_analysis"
    ]:
        return LLMProvider.OPENROUTER_FREE
    
    # TIER 2: Ollama Local (datos financieros)
    if task_type in [
        "pulso_analysis",
        "centinela_monitoring"
    ]:
        return LLMProvider.OLLAMA
    
    # TIER 3: Groq (crítico fiscal)
    if task_type in [
        "centinela_decision",
        "compliance_audit"
    ]:
        return LLMProvider.GROQ
    
    # Default: fallback seguro
    return LLMProvider.GROQ
```

---

### Paso 3: Crear Endpoints Que Usen Model Selector
**Archivo:** `apps/backend/presentation/agents_endpoints.py` (NEW)

Endpoints a crear:
1. `POST /api/v1/agents/pulso/analyze` → llama LLMEngine con task_type="pulso_analysis"
2. `POST /api/v1/agents/centinela/monitor` → task_type="centinela_monitoring"
3. `POST /api/v1/agents/centinela/decide` → task_type="centinela_decision"
4. `POST /api/v1/agents/taty/ask` → task_type="taty_faq"
5. `POST /api/v1/agents/social/generate-content` → task_type="social_content_gen"

Cada endpoint:
- Recibe request
- Extrae task_type
- Llama a `model_selector.choose_model_for_task(task_type)`
- Determina LLMProvider
- Llama a `get_ai_response(..., response_format="json")`
- Retorna respuesta

---

## RISK & MITIGATIONS

| Riesgo | Mitigation | Criticidad |
|--------|-----------|-----------|
| Ollama en Railway requiere GPU | Usar Railway GPU tier (~$50/mes extra) o fallback a OpenRouter Free | Media |
| OpenRouter Free tiene rate limits | OK para <100 req/día per tier 1; batch queries → Groq | Media |
| Latencia Ollama en respuestas grandes | Timeout inteligente: >2s → automático fallback a OpenRouter Free | Baja |
| Cliente se entera de cambio de modelo | NUNCA se entera — es cambio interno (LLMEngine, no API pública) | BAJA |
| Calidad Ollama insuficiente para Centinela critical | NO PERMITIR: Centinela Decision siempre usa Groq | Alta |

---

## VERIFICACIÓN (Post-Implementación)

- [ ] **Costos:** Factura OpenRouter + Railway antes/después (target: -50%)
- [ ] **Latencia:** P95 latency no sube >10% (medir con Pulso)
- [ ] **Calidad:** Respuestas Ollama vs Groq en Pulso (validar con cliente real)
- [ ] **Compliance:** Verify Centinela Fiscal SIEMPRE usa Groq (no Ollama)
- [ ] **Privacidad:** Verify datos financieros NUNCA enviados a OpenRouter (solo FAQ/social)

---

## SIGUIENTE: T2 - Integrar Ollama + OpenRouter Free

Archivos a crear/modificar:
1. Extend `llm_engine.py` con OLLAMA + OPENROUTER_FREE
2. Create `model_selector.py`
3. Create `agents_endpoints.py`
4. Update `router.py` to include agents_router
5. Create tests para failover

**Estimado:** 3-5 días
