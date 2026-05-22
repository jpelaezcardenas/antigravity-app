# PHASE 2: Silent Migration Integration — Frontend ↔ Backend

**Status:** Ready for Integration  
**Date:** 2026-05-22  
**Branch:** `feature/social-content-ops`  
**Backend:** ✅ All 8/8 endpoints 200 OK (tests passing)

---

## RESUMEN EJECUTIVO

El backend está **100% estable y listo**. Ahora necesitamos conectar el frontend (Antigravity Campaign Wizard, Kanban, Mobile PWA) a los endpoints reales del backend.

Esta es una **"migración muda"** (silent migration) porque:
- ✅ NO hay downtime
- ✅ NO hay datos perdidos
- ✅ Cambio gradual de mock → endpoints reales
- ✅ Rollback posible en cualquier momento si hay problemas

---

## PROCESO: 4 PASOS

### PASO 1: Verificar URLs y Credenciales Frontend

**Ubicación:** Frontend está en `C:\Users\contexia\Projects\antigravity-app\frontend/dashboard`

**Verificar:**
```bash
# 1. ¿Dónde está el frontend?
cd C:\Users\contexia\Projects\antigravity-app\frontend\dashboard
npm list  # Ver dependencias

# 2. ¿Está corriendo?
npm start  # Debería servir en http://localhost:3000 o http://localhost:5173
```

**Endpoints del backend activos:**
- Backend: `http://127.0.0.1:8000` (local) o `https://api.contexia.online` (producción)
- Todos los endpoints listados abajo (línea 30)

---

### PASO 2: Conectar Frontend a Backend Real

**Ubicación de config:** `frontend/dashboard/src/` (buscar `API_BASE_URL` o similar)

**Cambio necesario:**
```typescript
// ANTES (mock):
const API_BASE_URL = "http://localhost:3001/mock"; // ← Fake data

// DESPUÉS (real):
const API_BASE_URL = "http://127.0.0.1:8000/api/v1"; // ← Real backend
```

**Buscar estos archivos:**
- `src/hooks/useCampaignWizard.ts` (si existe)
- `src/hooks/useOrchestrator.ts` (si existe)
- `src/services/api.ts` o `src/utils/api.ts` (archivo central de API)
- `src/store/campaignStore.ts` o similar (Zustand store)

**Cambio en cada endpoint:**
```typescript
// ANTES:
const response = await fetch(`${API_BASE_URL}/campaigns/generate`, ...)

// DESPUÉS:
const response = await fetch(`http://127.0.0.1:8000/api/v1/agents/orchestrator/full-pipeline`, ...)
```

---

### PASO 3: Test de Conectividad

**Después de cambiar URLs, verificar que backend responde:**

```bash
# Test 1: Health Check
curl http://127.0.0.1:8000/api/v1/health

# Test 2: Full Pipeline (lo que Campaign Wizard llama)
curl -X POST http://127.0.0.1:8000/api/v1/agents/orchestrator/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://contexia.com",
    "campaign_objective": "Lead generation for tax audits",
    "budget": 5000,
    "target_channels": ["instagram", "linkedin"],
    "company_id": "31676930-b476-472b-bced-fd25f973cf8a"
  }'

# Test 3: Pulso Diario (Dashboard)
curl -X POST http://127.0.0.1:8000/api/v1/pulso/today \
  -H "Content-Type: application/json" \
  -d '{"company_id": "31676930-b476-472b-bced-fd25f973cf8a"}'
```

---

## MAPA DE ENDPOINTS FRONTEND → BACKEND

### 1. Campaign Wizard (Crear Campaña)

**Frontend Action:** User abre "Campaign Wizard" → hace click en "Generate"

**Frontend llama:**
```
POST /api/v1/agents/orchestrator/full-pipeline
```

**Request Body:**
```json
{
  "company_url": "https://ejemplo.com",
  "campaign_objective": "Aumentar leads para auditoría",
  "budget": 5000,
  "target_channels": ["instagram", "linkedin"],
  "company_id": "company-uuid-here"
}
```

**Response esperado (200 OK):**
```json
{
  "workflow_id": "pipeline-2026-05-22T...",
  "stages": [
    {
      "stage": "discovery",
      "agent": "onboarding",
      "status": "completed",
      "duration": "0.23s",
      "output": { "brand_identity": {...}, "colors": [...], "tone": "..." }
    },
    {
      "stage": "planning",
      "agent": "planner",
      "status": "completed",
      "duration": "0.45s",
      "output": { "campaign_options": [...] }
    },
    { ... 5 más agentes ... }
  ],
  "total_time": "2.5s",
  "generated_posts": [...]
}
```

**Frontend renderiza:** Kanban con posts generados por cada agente

---

### 2. Kanban / Campaign Board

**Frontend Action:** Kanban muestra posts generados

**Frontend llama:**
```
POST /api/v1/agents/orchestrator/full-pipeline
```

**Cada post tiene:**
- `id`: Identificador único
- `channel`: instagram | linkedin | twitter | tiktok
- `content`: Texto del post
- `image_url`: URL de imagen (si aplica)
- `status`: draft | approved | scheduled | published
- `compliance_score`: 0-100 (del Legal Reviewer)
- `variations`: Array de variaciones (del Repurposer)

---

### 3. Mobile PWA / Dashboard

**Frontend Action:** Usuario abre app mobile → ve "Pulso Diario" (8AM snapshot)

**Frontend llama:**
```
POST /api/v1/pulso/today
```

**Request:**
```json
{
  "company_id": "company-uuid-here"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "company_id": "...",
  "kpis": {
    "tax_filings_pending": 2,
    "compliance_status": "green",
    "alerts_count": 0,
    "audit_risk_score": 0.15
  },
  "snapshot_date": "2026-05-22"
}
```

---

### 4. Centinela Fiscal (Risk Alerts)

**Frontend Action:** Usuario abre "Alerts" en dashboard

**Frontend llama:**
```
GET /api/v1/centinela/alerts?company_id=company-uuid-here
```

**Response (200 OK):**
```json
{
  "status": "success",
  "company_id": "...",
  "total_alerts": 3,
  "alerts_by_severity": {
    "critical": [
      {
        "id": "alert-1",
        "type": "compliance_deadline_missed",
        "message": "Declaración de renta vencida hace 5 días",
        "severity": "critical"
      }
    ],
    "warning": [...],
    "info": [...]
  }
}
```

---

### 5. Taty RAG (Q&A)

**Frontend Action:** Usuario pregunta en chat (si está implementado)

**Frontend llama:**
```
POST /api/v1/taty/ask
```

**Request:**
```json
{
  "company_id": "company-uuid-here",
  "question": "¿Cuál es la fecha de vencimiento para renta 2025?",
  "language": "es"
}
```

**Response (200 OK):**
```json
{
  "status": "success" | "error",
  "question": "¿Cuál es la fecha de vencimiento para renta 2025?",
  "answer": "La fecha de vencimiento para la declaración de renta 2025 es...",
  "confidence": 0.95,
  "sources": ["dian.gov.co", "tax-guide-2025.pdf"]
}
```

---

## VERIFICACIÓN DE CONECTIVIDAD

### Test desde Frontend (Browser Console)

```javascript
// Test 1: Health Check
fetch('http://127.0.0.1:8000/api/v1/health')
  .then(r => r.json())
  .then(d => console.log('Health:', d))

// Test 2: Full Pipeline
fetch('http://127.0.0.1:8000/api/v1/agents/orchestrator/full-pipeline', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    company_url: 'https://contexia.com',
    campaign_objective: 'Test',
    budget: 5000
  })
})
  .then(r => r.json())
  .then(d => console.log('Pipeline:', d))

// Test 3: Pulso Today
fetch('http://127.0.0.1:8000/api/v1/pulso/today', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    company_id: '31676930-b476-472b-bced-fd25f973cf8a'
  })
})
  .then(r => r.json())
  .then(d => console.log('Pulso:', d))
```

---

## TROUBLESHOOTING

### Error: "Access to XMLHttpRequest blocked by CORS"

**Causa:** Frontend en puerto diferente, CORS no permite.

**Solución:** Backend CORS ya está configurado en `middleware_config.py`
- Permitidas: `http://localhost:5173` (Vite), `http://localhost:3000` (Next.js)
- Si frontend está en otro puerto, actualizar `.env` del backend:
```
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
```

### Error: "405 Method Not Allowed"

**Causa:** Endpoint llamado con método incorrecto (GET en un POST, etc.)

**Solución:** Verificar tabla de endpoints arriba. Ejemplos:
- ❌ `GET /api/v1/agents/orchestrator/full-pipeline` 
- ✅ `POST /api/v1/agents/orchestrator/full-pipeline`

### Error: "422 Unprocessable Entity"

**Causa:** Request body malformado o falta de parámetros requeridos.

**Solución:** Verificar que `company_id` está incluido en el request y es válido UUID.

### Error: "500 Internal Server Error"

**Causa:** Problema en el backend (LLM API no responde, DB no accesible, etc.)

**Solución:** 
- Ver logs del backend: `apps/backend/` (check console output)
- Verificar que Supabase está configurado en `.env`
- Verificar que LLM API keys están en `.env` (GROQ_API_KEY, etc.)

---

## TIMELINE DE INTEGRACIÓN

| Paso | Qué | Tiempo | Blocker? |
|------|-----|--------|----------|
| 1 | Verificar frontend está corriendo | 5 min | ❌ |
| 2 | Cambiar API_BASE_URL a backend real | 10 min | ❌ |
| 3 | Verificar conectividad (curl tests) | 5 min | ✅ Si falla |
| 4 | Test Campaign Wizard → /full-pipeline | 10 min | ✅ Si falla |
| 5 | Test Dashboard → /pulso/today | 5 min | ✅ Si falla |
| 6 | Test Centinela → /centinela/alerts | 5 min | ✅ Si falla |
| 7 | Test Taty → /taty/ask (si implementado) | 5 min | ❌ (no crítico) |
| 8 | Demo en vivo con usuario final | 30 min | ❌ |

**Total: ~75 minutos**

---

## CHECKLIST: LISTO PARA DEMO EN VIVO

- [ ] Backend corriendo en puerto 8000 (`uvicorn main:app`)
- [ ] Frontend corriendo en puerto 3000 o 5173
- [ ] API_BASE_URL cambió a `http://127.0.0.1:8000/api/v1`
- [ ] Health check responde 200 OK
- [ ] Full Pipeline responde 200 OK con 7 agentes
- [ ] Pulso Today responde 200 OK con KPIs
- [ ] Centinela Alerts responde 200 OK con alertas vacías (o datos demo)
- [ ] Frontend puede hacer POST a /orchestrator/full-pipeline sin errores CORS
- [ ] Kanban renderiza posts generados por backend
- [ ] Dashboard (Mobile PWA) muestra Pulso Diario KPIs
- [ ] Demo data cargada en Supabase (3 clientes demo)

---

## DEMOSTRACIÓN EN VIVO: 4 SEGMENTOS

Una vez todo está conectado, ejecutar demo con estos 4 segmentos:

### SEGMENT 1: Pulso Diario (8AM Snapshot)
- **Qué:** Dashboard muestra KPIs de empresa
- **Cómo:** Mobile PWA abre → ve "Pulso Diario" con 5 métricas
- **Endpoint:** `POST /api/v1/pulso/today`
- **Duración:** 30 seg
- **Resultado:** KPIs mostrados (tax filings, compliance, risks, audit score)

### SEGMENT 2: Centinela Fiscal (Risk Alerts)
- **Qué:** Sistema detecta riesgos fiscales
- **Cómo:** Dashboard muestra lista de alertas by severity
- **Endpoint:** `GET /api/v1/centinela/alerts`
- **Duración:** 20 seg
- **Resultado:** Alertas críticas destacadas en rojo

### SEGMENT 3: Taty Q&A (RAG)
- **Qué:** Asistente responde preguntas fiscales
- **Cómo:** Usuario pregunta "¿Cuál es fecha vencimiento renta 2025?"
- **Endpoint:** `POST /api/v1/taty/ask`
- **Duración:** 30 seg
- **Resultado:** Respuesta con fuentes y confianza

### SEGMENT 4: Full Pipeline (7 Agentes)
- **Qué:** Orquestador ejecuta 7 agentes en cascada
- **Cómo:** Campaign Wizard generador → click "Generate" → ver Kanban con posts
- **Endpoint:** `POST /api/v1/agents/orchestrator/full-pipeline`
- **Duración:** 2-3 seg (backend) + UI rendering
- **Resultado:** Kanban con 3+ variaciones de posts, cada una con status + compliance score

---

## PRÓXIMOS PASOS DESPUÉS DE DEMO

1. **Feedback del cliente:** Qué les gustó, qué mejorar
2. **Semana 2 (Week 2):**
   - Real Meta Instagram API integration (Distribution Agent)
   - Real LinkedIn API integration
   - DIAN/ERP manual import workflow
   - Multi-client scaling
3. **Semana 3 (Week 3):**
   - Analytics dashboard (post performance tracking)
   - A/B testing de variaciones
   - Scheduling automático

---

## CONTACTO & SOPORTE

- **Backend Code:** `apps/backend/`
- **API Docs:** `http://127.0.0.1:8000/docs` (cuando backend está corriendo)
- **Tests:** `apps/backend/test_endpoint_fix.py`
- **Logs:** Console output de Uvicorn
- **Issues:** Si endpoint falla, check console output backend + curl test

---

**Prepared by:** Claude (AI Assistant)  
**Status:** Ready for Frontend Team Integration  
**Last Updated:** 2026-05-22 09:50 UTC
