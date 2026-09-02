# Spec: hermes-jarvis-contexia

**Change:** hermes-jarvis-contexia  
**Fecha:** 2026-09-01

---

## Fase A — Jarvis Personal por Telegram

### Tarea 1: Crear `apps/backend/presentation/jarvis_endpoints.py`

**Archivo nuevo.** Estructura clave:

- `JarvisRouter` class con métodos:
  - `handle_webhook()` — valida HMAC-SHA256, extrae mensaje Telegram, proxy a Hermes
  - `brief_endpoint()` — agrega Caja Real + alertas + Approval Queue (POST /api/v1/jarvis/brief)
  - `chat_proxy()` — reenvía chat desde Búnker a Hermes (POST /api/v1/jarvis/chat)
  - `status_proxy()` — health check del gateway (GET /api/v1/jarvis/status, admin only)
  - `_resolve_hermes_gateway()` — lee hermes_tunnel[id='current'] de Supabase

Validaciones:
- HMAC signature debe coincidir con TELEGRAM_WEBHOOK_SECRET_JARVIS
- Timeout a Hermes: 5s max, devolver 504 si excede
- Mensaje Telegram vacío: ignorar silenciosamente (return 200)
- Hermes offline: log error, devolver reply genérico

Tests: webhook_invalid_sig, webhook_valid, brief_endpoint, status_online/offline

---

### Tarea 2: Registrar router en `apps/backend/presentation/router.py`

**Editar línea ~5:**
```python
from .jarvis_endpoints import JarvisRouter

# En función main:
jarvis = JarvisRouter()
app.include_router(jarvis.router)
```

---

### Tarea 3: Actualizar `apps/backend/config.py`

**Agregar env vars:**
```
TELEGRAM_BOT_TOKEN_JARVIS = os.getenv("TELEGRAM_BOT_TOKEN_JARVIS", "")
TELEGRAM_WEBHOOK_SECRET_JARVIS = os.getenv("TELEGRAM_WEBHOOK_SECRET_JARVIS", "")
TELEGRAM_JUAN_DAVID_CHAT_ID = os.getenv("TELEGRAM_JUAN_DAVID_CHAT_ID", "")
JARVIS_ENABLED = bool(TELEGRAM_BOT_TOKEN_JARVIS)
```

---

### Tarea 4: Railway env vars

Setear en https://railway.app (service antigravity-app):
- TELEGRAM_BOT_TOKEN_JARVIS
- TELEGRAM_WEBHOOK_SECRET_JARVIS
- TELEGRAM_JUAN_DAVID_CHAT_ID

Valores obtenidos de Bitwarden por el fundador.

---

### Tarea 5: Registrar webhook en Telegram

**Acción manual del fundador.** Desde terminal:
```bash
curl -X POST https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN_JARVIS/setWebhook \
  -d url="https://antigravity-app-production-175a.up.railway.app/api/v1/channels/jarvis/webhook" \
  -d secret_token="$TELEGRAM_WEBHOOK_SECRET_JARVIS"
```

Verificar respuesta: `{"ok":true}`

---

### Tarea 6: Crear `~/.hermes/profiles/contexia/skills/jarvis-personal.md`

**Archivo nuevo.** Skill definition:
- Identidad: "Jarvis Personal — Contexia Operaciones"
- Contexto: acceso financiero + comercial, tono ejecutivo
- Herramientas: Caja Real, Centinela, HubSpot, Gmail, Meta
- Comportamiento: brief matutino 9 AM, chat ad-hoc

---

### Tarea 7: Crear cron `~/.hermes/scripts/jarvis-morning-brief.sh`

**Bash script que:**
1. Llama POST /api/v1/jarvis/brief (Railway) con token HERMES_BRIDGE_TOKEN
2. Llama GET /sell-machine/tasks/recent?hours=24 (Manus local)
3. Agrega contexto + redacta brief via Hermes skill
4. Envía a Telegram TELEGRAM_JUAN_DAVID_CHAT_ID

Timeouts: 5s por llamada, fail-graceful omite sección si falla.

**Registrar en `~/.hermes/jobs.json`:**
```json
{
  "id": "jarvis-morning-brief",
  "schedule": "0 9 * * *",
  "script": "scripts/jarvis-morning-brief.sh",
  "timeout_seconds": 60,
  "retry_on_failure": true,
  "retry_count": 3,
  "enabled": true
}
```

---

### Tarea 8: Smoke test Fase A

**Manual verification:**
1. Enviar POST a /api/v1/channels/jarvis/webhook con payload Telegram válido
   - Esperado: mensaje en Telegram de respuesta
2. Enviar POST a /api/v1/jarvis/brief con token Bearer
   - Esperado: JSON con caja_real, alertas, approval_queue_pending
3. Verificar Manus API accesible desde Hermes
   - Esperado: GET /sell-machine/tasks/recent devuelve deals + emails + ads

---

## Fase B — Búnker Agentic OS

### Tarea 9: Crear componentes en `contexia-app/components/bunker/agentic-os/`

**5 archivos nuevos:**

1. `AgenticOsSection.tsx` — sección principal, feature-gated por hasFeature("jarvis_chat")
2. `HermesStatusCard.tsx` — muestra online/offline + URL gateway, refresh cada 30s
3. `JarvisChatInterface.tsx` — chat bidireccional (input + messages, POST /api/v1/jarvis/chat)
4. `CronJobsMonitor.tsx` — lista de cron jobs (stub: solo mostra jarvis-morning-brief próxima ejecución)
5. `VoiceToggle.tsx` — botón WebSpeechAPI (solo si hasFeature("jarvis_voice"))

Todos reutilizan `authenticatedFetch` y manejan errores gracefully.

---

### Tarea 10: Crear `contexia-app/lib/jarvis-client.ts`

**Métodos:**
- `chat(message, tenantId)` → POST /api/v1/jarvis/chat
- `status()` → GET /api/v1/jarvis/status

Ambos usan `authenticatedFetch`.

---

### Tarea 11: Actualizar `contexia-app/lib/config.ts`

**Agregar:**
```typescript
JARVIS_CHAT_URL: "/api/v1/jarvis/chat"
JARVIS_STATUS_URL: "/api/v1/jarvis/status"
```

---

### Tarea 12: Actualizar `contexia-app/app/app/bunker/page.tsx`

**Editar:**
```typescript
// De:
const PLACEHOLDER_SECTIONS: BunkerSection[] = ["agentic-os", "configuracion"];

// A:
const PLACEHOLDER_SECTIONS: BunkerSection[] = ["configuracion"];
```

---

## Fase C — Tier display y feature gating

### Tarea 13: Actualizar `apps/backend/core/plan_features.py`

```python
PLAN_FEATURES = {
    "freemium": frozenset({"pulso_diario"}),
    "starter": frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge"}),
    "growth": frozenset({
        "pulso_diario", "centinela_alerts", "liquidity_bridge", 
        "jarvis_chat"
    }),
    "enterprise": frozenset({
        "pulso_diario", "centinela_alerts", "liquidity_bridge", 
        "jarvis_chat", "jarvis_voice"
    }),
}
```

---

### Tarea 14: Display names en `contexia-app/components/config/TenantInfoCard.tsx`

**Agregar mapping:**
```typescript
const TIER_DISPLAY: Record<PlanTier, string> = {
  "freemium": "Pulso Básico",
  "starter": "Pulso Básico",
  "growth": "GPS Financiero",
  "enterprise": "Contexia Total",
};

// Usar: {TIER_DISPLAY[tenant.plan_tier]}
```

---

### Tarea 15: Messaging en `contexia-app/components/shared/UpgradePlanBanner.tsx`

**Agregar copy específico para tier:**
- growth CTA: "Acceso a Jarvis" con pricing
- enterprise CTA: "Acceso a Jarvis con voz" con pricing

---

## Stage 11: Deploy to Production

**Checklist:**
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build green
- [ ] 11.3 Railway deploy active
- [ ] 11.4 Test en producción: Telegram webhook funciona, Búnker Agentic OS visible
- [ ] 11.5 Crear reporte: openspec/changes/hermes-jarvis-contexia/reports/YYYY-MM-DD-deployment.md
