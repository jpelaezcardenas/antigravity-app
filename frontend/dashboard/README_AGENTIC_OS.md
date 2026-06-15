# Contexia Agentic OS – Agentic Ops

Este documento describe la capa de **Agentic Operating System (Agentic OS)** integrada en el Bunker de Contexia, expuesta en la vista **Agentic Ops**.

La idea central: el frontend y backend de Contexia siguen siendo la fuente de verdad, y Hermes Agent se conecta como motor de orquestación, análisis y automatización.

---

## 1. Objetivo de Agentic Ops

Agentic Ops es el “panel de mando” donde se cruzan:

- El estado vivo de la infraestructura Contexia (Vercel → FastAPI Railway → Supabase).
- El estado y comportamiento del perfil Hermes `contexia` (modelo, skills, cronjobs, LLM failover).
- La capa de inteligencia continua (daily brief, insights, costos de IA, artefactos).

No es un reemplazo del Bunker ni del dashboard de negocio: es una vista para operar el **sistema de agentes** que vive alrededor del producto.

---

## 2. Arquitectura básica

### 2.1 Frontend

- Vista: `Agentic Ops` en el sidebar del Bunker.
- Ruta pública recomendada:

  - `/app/bunker/agentic-ops`

- Implementación:

  - Componente React/TypeScript en `frontend/dashboard/src/.../AgenticOpsPage.tsx`.
  - Consume APIs de:
    - Backend Contexia (`/api/v1/*`).
    - Gateway de Hermes (`/webhooks/os/*`).

### 2.2 Backend Contexia (FastAPI)

- Sigue siendo el runtime canon para:
  - `/api/v1/health`
  - `/api/v1/social-ops/*`
  - `/api/v1/pulso`, `/api/v1/centinela/*`
  - Wizard, KB, Radar, etc.
- Agentic Ops solo **lee** estos endpoints (y opcionalmente dispara acciones documentadas) para mostrar estado y métricas.

### 2.3 Backend Hermes (perfil `contexia`)

- Hermes Agent corre con:

  - Perfil: `contexia`
  - Toolsets mínimos: `terminal`, `file`, `web`, `skills`, `memory`, `delegation`, `cronjob`.
  - Gateway HTTP habilitado (puerto configurable).

- Skills principales:

  - `contexia-core`: orquestador de agentes (Discovery / Planner / Generator) y wrapper `call_llm_contexia`.
  - `contexia-llm-failover`: motor LLM multi‑proveedor (Groq → Cerebras → Mistral → Gemini → OpenRouter) con parser robusto.
  - `contexia-os`: backend del Agentic OS (webhooks `/os/status`, futuros `/os/dream-latest`, `/os/usage`, etc.).
  - `contexia-dreams` (planeado): generación del “Contexia Daily Brief” vía cron.

---

## 3. Endpoints clave

### 3.1 Hermes → `/webhooks/os/status`

- Proveedor: Gateway Hermes (perfil contexia).
- Método: `GET`
- Descripción: devuelve un snapshot combinado de Contexia + Hermes.

**Esquema mínimo esperado:**

```json
{
  "generated_at": "2026-06-04T10:00:00Z",
  "contexia": {
    "api_health": "healthy",
    "api_latency_ms": 120,
    "social_ops": {
      "ideas_source": "supabase",
      "metrics_source": "supabase"
    }
  },
  "hermes": {
    "profile": "contexia",
    "model": "openrouter/<modelo>",
    "skills": ["contexia-core", "contexia-os"]
  }
}
```

La vista Agentic Ops lo usa para renderizar:

- Tarjeta “Backend Contexia”.
- Tarjeta “Hermes status”.

### 3.2 Contexia → `/api/v1/health`

- Proveedor: FastAPI (Railway, expuesto via Vercel).
- Método: `GET`
- Uso en Agentic Ops:
  - Determinar si la API está `healthy`, `degraded` o `down`.
  - Medir latencia.

### 3.3 Contexia → `/api/v1/social-ops/ideas` y `/metrics`

- Proveedor: FastAPI Social Ops.
- Método: `GET`
- Uso en Agentic Ops:
  - Verificar que Social Ops esté leyendo de Supabase (no de memoria demo).
  - Mostrar `source` y estado de las tablas.

---

## 4. Flujo de datos en la vista Agentic Ops

1. El usuario abre `/app/bunker/agentic-ops`.
2. El frontend:
   - Llama `GET /webhooks/os/status` al gateway Hermes.
   - (Opcional) Llama directamente a `/api/v1/health` si se requiere validar algo más.
3. Hermes, a través del skill `contexia-os`, consulta las APIs de Contexia y arma el JSON de status.
4. El Bunker renderiza:
   - Estado del backend (semáforo, latencia, fuentes Social Ops).
   - Estado de Hermes (perfil, modelo activo, skills contexia registrados).
   - Timestamp de generación.

En versiones futuras, Agentic Ops también mostrará:

- Último “Contexia Daily Brief”.
- Métricas de tokens/costos por proveedor.
- Artefactos recientes generados por Hermes (specs, reportes Stage 11, etc.).

---

## 5. Principios de diseño

- **No romper la arquitectura actual**:
  - El hosting sigue siendo Vercel (frontend) + Railway (FastAPI) + Supabase.
  - Hermes se trata como un microservicio externo más, expuesto vía HTTP.

- **Spec‑first y Stage 11**:
  - Cualquier ampliación significativa de Agentic Ops debe pasar por OpenSpec y Stage 11 antes de llegar a producción.

- **Seguridad y límites de negocio**:
  - Agentic Ops puede sugerir acciones, nunca “firmar” decisiones fiscales o legales.
  - Datos sensibles se leen vía backend; la vista no debe exponer secretos ni claves.

---

## 6. Checklist para nuevos contribuidores

Antes de tocar Agentic Ops:

1. Leer:
   - `PROFILE.md` del perfil Hermes `contexia`.
   - Este `README_AGENTIC_OS.md`.
   - OpenSpec/ai‑specs relevantes y Stage 11 del cambio.
2. Verificar:
   - Gateway Hermes corriendo y accesible.
   - `/api/v1/health` `200 healthy` en entorno correspondiente.
3. Trabajar siempre en:
   - Rama de feature dedicada.
   - Cambios pequeños, probados localmente, con plan Stage 11 documentado.