# Design: hermes-jarvis-contexia

**Change:** hermes-jarvis-contexia  
**Fecha:** 2026-09-01  
**Estado:** design (detalla implementación de cada fase)

---

## Decisiones de arquitectura

### D1: Brief matutino = dos llamadas HTTP en paralelo

**Decisión:** Hermes hace dos llamadas **no bloqueantes** (paralelo/async):
1. `POST /api/v1/jarvis/brief` (Railway) → contexto financiero
2. `GET /sell-machine/tasks/recent?hours=24` (Manus local) → contexto comercial

**Por qué:** evita la latencia de esperar a una si la otra es lenta; fail-graceful si una falla.

**Implementación:** Hermes bash script usa `curl` con timeout y captura errores; cada falla logea pero no bloquea.

---

### D2: Hermes accede a Manus localmente, no via Railway

**Decisión:** La URL de Manus (`http://localhost:MANUS_PORT/api/...`) vive en `~/.hermes/config.yaml`, no en env vars de Railway.

**Por qué:** soberanía de datos; las credenciales de Manus nunca tocan Railway.

---

### D3: Brief es sync y encolable

**Decisión:** El cron ejecuta el script de forma **síncrona** (espera respuesta de ambas fuentes antes de redactar).
Si alguna tarda >5s, timeout y omite esa sección.

**Por qué:** el fundador quiere un brief completo cada mañana, no parcial.

---

### D4: Telegram webhook + gateway dinámico

**Decisión:** el webhook vive en Railway (`POST /api/v1/channels/jarvis/webhook`), pero resuelve dinámicamente
la URL de Hermes desde `hermes_tunnel[id='current']` en Supabase (reutiliza el patrón de `/api/hermes/status.ts`).

---

## Fase A — Jarvis Personal por Telegram

### A1: Backend `jarvis_endpoints.py`

Estructura:
- `handle_webhook()` — valida token Telegram, reenvía a Hermes
- `brief_endpoint()` — agrega contexto financiero para cron matutino
- `chat_proxy()` — proxy de chat desde Búnker a Hermes
- `status_proxy()` — health check del gateway (admin only)

Patrones:
- Reutilizar `resolve_hermes_gateway_url()` (como en `/api/hermes/status.ts`)
- Validación de token Telegram (HMAC-SHA256)
- Timeouts a Hermes: >5s → 504
- Error handling: log y devolver graceful

### A2: Config en `apps/backend/config.py`

Agregar:
```
TELEGRAM_BOT_TOKEN_JARVIS
TELEGRAM_WEBHOOK_SECRET_JARVIS
TELEGRAM_JUAN_DAVID_CHAT_ID
JARVIS_ENABLED = bool(TELEGRAM_BOT_TOKEN_JARVIS)
```

### A3: Router en `apps/backend/presentation/router.py`

Registrar JarvisEndpoints router bajo `/jarvis`.

### A4: Hermes skill `jarvis-personal.md`

Define identidad, contexto, herramientas del asistente personal.

### A5: Cron `jarvis-morning-brief.sh`

Bash script que:
- Llama Railway (`POST /api/v1/jarvis/brief`) → financiero
- Llama Manus (`GET /sell-machine/tasks/recent?hours=24`) → comercial
- Agrega contexto + redacta brief via Hermes skill
- Envía a Telegram

Timeout: 5s por llamada, fail-graceful omite sección.

Registrar en `jobs.json` con schedule `0 9 * * *` (9 AM COT diario).

---

## Fase B — Búnker Agentic OS

### B1: Components en `contexia-app/components/bunker/agentic-os/`

- `AgenticOsSection.tsx` — sección principal, feature-gated por tier
- `HermesStatusCard.tsx` — health del gateway + agentes activos
- `JarvisChatInterface.tsx` — chat bidireccional (POST /api/v1/jarvis/chat)
- `CronJobsMonitor.tsx` — lista de cron jobs + último estado
- `VoiceToggle.tsx` — Web Speech API (solo enterprise)

### B2: Client `jarvis-client.ts`

Métodos:
- `chat(message, tenantId)` → POST /api/v1/jarvis/chat
- `status()` → GET /api/v1/jarvis/status

### B3: Config endpoints en `contexia-app/lib/config.ts`

```
JARVIS_CHAT_URL: "/api/v1/jarvis/chat"
JARVIS_STATUS_URL: "/api/v1/jarvis/status"
```

### B4: Update `contexia-app/app/app/bunker/page.tsx`

Quitar "agentic-os" de `PLACEHOLDER_SECTIONS`.

---

## Fase C — Tier display y feature gating

### C1: Feature flags en `plan_features.py`

```python
"growth": {..., "jarvis_chat"}
"enterprise": {..., "jarvis_chat", "jarvis_voice"}
```

### C2: Display names en `TenantInfoCard.tsx`

```
freemium/starter → "Pulso Básico"
growth → "GPS Financiero"
enterprise → "Contexia Total"
```

### C3: Messaging en `UpgradePlanBanner.tsx`

Copy con pricing y feature unlock específico.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Hermes gateway offline | Cron falla, alert a Slack, retry 3 veces |
| Manus timeout | Brief omite sección comercial, envía parcial |
| Telegram token expuesto | En Bitwarden, rotar antes de deploy |

---

## Dependencias

```
Stage 0 (Prerequisites) → Fase A → Fase B → Fase C → Stage 11 (Deploy)
```

---

## Próximo: Spec (detalla qué código escribir por tarea)
