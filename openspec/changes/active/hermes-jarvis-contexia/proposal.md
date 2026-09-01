# Proposal: hermes-jarvis-contexia

**ID:** hermes-jarvis-contexia
**Fecha:** 2026-09-01
**Estado:** proposed
**Autor:** Juan David Peláez / Contexia

---

## Problem statement

Contexia opera 11 clientes activos con datos financieros reales. El fundador necesita:

1. **Un asistente personal de mando** (Jarvis) accesible desde Telegram — con acceso a todos los tenants, métricas, memoria de Hermes y tools de agente — sin depender del navegador.
2. **Una sección "Agentic OS" real en el Búnker** — actualmente marcada como "coming soon" en `PLACEHOLDER_SECTIONS`. Los clientes B2B tier Growth/Enterprise deben ver su propio Jarvis ahí.
3. **Tier gating coherente con el pricing publicado** — hoy `plan_features.py` da a `growth` y `enterprise` exactamente las mismas features que `starter`; el pricing ya está definido pero el código no lo refleja.

---

## Proposed solution

Construir "Hermes Jarvis" en cuatro fases incrementales:

### Fase A — Jarvis Personal por Telegram (prioridad máxima)

Nuevo bot de Telegram (`TELEGRAM_BOT_TOKEN_JARVIS`) separado del bot de Taty. Webhook en:
`POST /api/v1/channels/jarvis/webhook`

El backend extrae el mensaje, llama al gateway de Hermes (resuelto dinámicamente desde la tabla
`hermes_tunnel` en Supabase — **no** una env var estática, el mismo patrón de
`api/hermes/status.ts`), y reenvía la respuesta al chat del fundador.

**Hermes gateway:** port `:8644`, URL dinámica mantenida por `tunnel_persistent.ps1` (ya
operativo con auto-start vía VBS en Windows Startup). La URL se guarda en
`hermes_tunnel[id='current']` — Railway la lee con `SUPABASE_ANON_KEY` en cada request.

**Brief matutino proactivo:** nuevo cron Hermes `jarvis-morning-brief.sh` (9:00 AM COT),
llama a `POST /api/v1/jarvis/brief` → Hermes genera resumen de Caja Real + alertas Centinela
+ tareas pendientes → envía al `TELEGRAM_JUAN_DAVID_CHAT_ID`.

**Nuevas env vars en Railway:**
- `TELEGRAM_BOT_TOKEN_JARVIS`
- `TELEGRAM_WEBHOOK_SECRET_JARVIS`
- `TELEGRAM_JUAN_DAVID_CHAT_ID`
- `SUPABASE_ANON_KEY` (probablemente ya existe — para resolver URL dinámica de Hermes)
- `HERMES_BRIDGE_TOKEN` (ya existe — autentica calls a Hermes)

### Fase B — Búnker Agentic OS (UI)

Reemplazar `ComingSoonSection` para "agentic-os" en `contexia-app/app/app/bunker/page.tsx`.

Remover de `PLACEHOLDER_SECTIONS`:
```ts
// De:
const PLACEHOLDER_SECTIONS: BunkerSection[] = ["agentic-os", "configuracion"];
// A:
const PLACEHOLDER_SECTIONS: BunkerSection[] = ["configuracion"];
```

Nuevos componentes en `contexia-app/components/bunker/agentic-os/`:
- `AgenticOsSection.tsx` — sección principal (patrón: `MetricsDashboardSection`)
- `HermesStatusCard.tsx` — health del gateway + agentes activos
- `JarvisChatInterface.tsx` — chat → `POST /api/v1/jarvis/chat`
- `CronJobsMonitor.tsx` — lista de cron jobs de Hermes + último estado
- `VoiceToggle.tsx` — browser Web Speech API (Fase 1, sin dependencias)

Nuevos endpoints backend:
- `GET /api/v1/jarvis/status` — proxy a Hermes `/health` (solo admin)
- `POST /api/v1/jarvis/chat` — proxy del mensaje al gateway de Hermes, streaming

Nuevo cliente tipado: `contexia-app/lib/jarvis-client.ts` (reutiliza `authenticatedFetch`)

**Feature gating en Agentic OS:**
- `freemium` → estado bloqueado con CTA de upgrade
- `starter` → estado bloqueado con CTA de upgrade
- `growth` → chat completo, texto
- `enterprise` → chat completo + modo voz

**Nota de arquitectura:** "agentic-os" NO va a `ADMIN_ONLY_SECTIONS` — per ARCHITECTURE.md
Decisión #18, los clientes B2B ven Dashboard + Agentic OS + Configuración. El feature gating
es por plan tier inside the component.

### Fase C — Tier display y feature gating fino

Actualizar display names en el frontend (no migrar claves de BD en este change):

| Clave BD actual | Display nuevo |
|---|---|
| `freemium` | "Pulso Básico" |
| `starter` | "Pulso Básico" (mismo display, misma clave) |
| `growth` | "GPS Financiero" |
| `enterprise` | "Contexia Total" |

Agregar feature flags faltantes en `plan_features.py`:
```python
PLAN_FEATURES = {
    "freemium":   frozenset({"pulso_diario"}),
    "starter":    frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge"}),
    "growth":     frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge", "jarvis_chat"}),
    "enterprise": frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge", "jarvis_chat", "jarvis_voice"}),
}
```

Actualizar display en:
- `contexia-app/components/config/TenantInfoCard.tsx`
- `contexia-app/components/shared/UpgradePlanBanner.tsx`

### Fase D — Customer Jarvis por Telegram (Fase 2, post-validación)

Extensión del bot de Taty existente: si el mensaje inbound viene de un tenant con
`plan_tier in (growth, enterprise)`, se enruta a Hermes (con contexto del tenant) en vez de
a Taty básico. **No requiere un nuevo bot.** Esta fase tiene su propio OpenSpec change separado
— depende de que la Fase A valide el roundtrip Telegram → Hermes → response.

---

## Out of scope (este change)

- Llamadas telefónicas (Twilio) — change futuro separado
- Integraciones Google Calendar/Gmail vía n8n — prohibido por AGENTES.md Regla 4
- Renombrar claves de BD (`growth` → `pro`, `freemium` → `free`) — migración de base de datos separada; solo se cambia el display en UI aquí
- VoiceBox proxy script — Fase 2, después de que Fase B esté en producción
- Multi-tenant Telegram routing (Fase D) — change separado

---

## Patrones a reutilizar (no reinventar)

| Patrón | Origen |
|---|---|
| Webhook handler de Telegram | `apps/backend/presentation/telegram_endpoints.py` |
| Verificación de token Hermes | `apps/backend/core/hermes_auth.py::verify_hermes_token` |
| `has_feature()` y `plan_features.py` | `apps/backend/core/plan_features.py` |
| `authenticatedFetch` | `contexia-app/lib/authenticated-fetch.ts` |
| Patrón de sección del Búnker | `contexia-app/components/bunker/metrics/MetricsDashboardSection.tsx` |
| Self-feeding card pattern | `contexia-app/components/bunker/metrics/QueueHealthCard.tsx` |
| Resolución dinámica de URL Hermes | `contexia-app/app/api/hermes/status.ts` (leer `hermes_tunnel` de Supabase) |

---

## Archivos críticos

### Backend — nuevos o modificados
| Archivo | Acción |
|---|---|
| `apps/backend/presentation/jarvis_endpoints.py` | CREAR — webhook Telegram + proxies chat/status/brief |
| `apps/backend/presentation/router.py` | MODIFICAR — registrar router de Jarvis |
| `apps/backend/core/plan_features.py` | MODIFICAR — agregar `jarvis_chat`, `jarvis_voice` |
| `apps/backend/config.py` | MODIFICAR — agregar `TELEGRAM_BOT_TOKEN_JARVIS`, `TELEGRAM_WEBHOOK_SECRET_JARVIS`, `TELEGRAM_JUAN_DAVID_CHAT_ID` |

### Frontend — nuevos o modificados
| Archivo | Acción |
|---|---|
| `contexia-app/components/bunker/agentic-os/AgenticOsSection.tsx` | CREAR |
| `contexia-app/components/bunker/agentic-os/HermesStatusCard.tsx` | CREAR |
| `contexia-app/components/bunker/agentic-os/JarvisChatInterface.tsx` | CREAR |
| `contexia-app/components/bunker/agentic-os/CronJobsMonitor.tsx` | CREAR |
| `contexia-app/components/bunker/agentic-os/VoiceToggle.tsx` | CREAR |
| `contexia-app/lib/jarvis-client.ts` | CREAR |
| `contexia-app/lib/config.ts` | MODIFICAR — agregar `JARVIS_CHAT`, `JARVIS_STATUS` |
| `contexia-app/app/app/bunker/page.tsx` | MODIFICAR — quitar "agentic-os" de `PLACEHOLDER_SECTIONS` |
| `contexia-app/components/config/TenantInfoCard.tsx` | MODIFICAR — display names por tier |
| `contexia-app/components/shared/UpgradePlanBanner.tsx` | MODIFICAR — copy con pricing real |

### Hermes (WSL) — nuevos
| Archivo | Acción |
|---|---|
| `~/.hermes/profiles/contexia/skills/jarvis-personal.md` | CREAR — identidad y contexto del Jarvis personal |

### Infraestructura
| Recurso | Acción |
|---|---|
| Railway env vars | AGREGAR las 3-4 variables nuevas listadas arriba |
| Telegram @BotFather | CREAR bot nuevo — acción del fundador, no de código |
| Telegram webhook | REGISTRAR en `https://antigravity-app-production-175a.up.railway.app/api/v1/channels/jarvis/webhook` |

---

## Verification

1. **Jarvis Telegram:** mensaje al bot nuevo → respuesta de Hermes → Railway logs muestran el roundtrip
2. **Agentic OS:** login al Búnker → click "Agentic OS" → HermesStatusCard visible (no "coming soon") + CronJobsMonitor con 8 jobs listados
3. **Jarvis chat en Búnker:** pregunta en el chat → respuesta de Hermes
4. **Tier display:** Config page muestra "GPS Financiero" en vez de "Growth" para un tenant `growth`
5. **Feature gate:** tenant `freemium` ve Jarvis bloqueado con CTA; tenant `growth` ve chat completo
6. **Voz (Fase B):** click en micrófono → browser speech recognition activa → transcripción enviada a Jarvis
7. **No regressions:** Dashboard metrics, Social Ops, CRM, Sell Machine no se ven afectados

---

## Prerequisitos del fundador (acciones no-código, previas a la implementación)

1. Crear bot nuevo en Telegram vía @BotFather → obtener `TELEGRAM_BOT_TOKEN_JARVIS`
2. Obtener su propio `TELEGRAM_JUAN_DAVID_CHAT_ID` (enviar `/start` al bot y ver el chat_id en los logs del webhook de prueba)
3. Confirmar que `tunnel_persistent.ps1` está corriendo y que la tabla `hermes_tunnel[id='current']` tiene una URL válida en Supabase

---

## Notas sobre Manus y el brief matutino

El brief matutino de Jarvis puede agregar contexto de Manus (pipeline de HubSpot, resumen de Gmail, performance de Meta) vía una llamada HTTP al API interno de Manus. El alcance de este change es exclusivamente el roundtrip Telegram → Hermes → response y el brief básico (Caja Real + alertas). La integración bidireccional completa Hermes ↔ Manus es un change separado.
