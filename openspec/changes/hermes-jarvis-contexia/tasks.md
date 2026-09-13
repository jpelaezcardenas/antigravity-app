# Tasks: hermes-jarvis-contexia

**Change:** hermes-jarvis-contexia
**Estado:** in_progress (re-scoped 2026-09-13 por `HANDOFF.md` — un solo bot de Telegram, D1-D13)

> **Nota de reconciliación 2026-09-13:** este archivo estaba desactualizado (marcaba 0/28 aunque
> las tareas 1-3 ya estaban codificadas en `main`, commit `45fd4af`, usando un segundo bot de
> Telegram). El hilo de esa fecha decidió (D1, `HANDOFF.md` §2) fusionar todo en el bot único de
> Taty en vez de mantener `TELEGRAM_BOT_TOKEN_JARVIS`. Las tareas 1-3 originales (crear
> `jarvis_endpoints.py`, registrar router, agregar env vars) se dan por **hechas en su forma
> original**, pero la Fase 1 de abajo las **reemplaza parcialmente** (elimina el webhook y las
> env vars del segundo bot). Ver `HANDOFF.md` para las decisiones D1-D13 completas.

---

## Stage 0. Prerequisitos del fundador (no-código) — RE-ESCRITO por D1

- [x] 0.1 ~~Crear bot nuevo en Telegram via @BotFather~~ — **YA NO APLICA (D1)**: un solo bot,
      el de Taty (`TELEGRAM_BOT_TOKEN` existente). Ningún bot nuevo que crear.
- [ ] 0.2 Obtener `TELEGRAM_JUAN_DAVID_CHAT_ID` del chat personal del fundador (enviar `/start`
      al bot de Taty, leer el `chat_id` en logs de Railway) y setearlo en Railway — **founder action**
- [ ] 0.3 Confirmar que `tunnel_persistent.ps1` corre y que `hermes_tunnel[id='current']` tiene URL
      válida en Supabase
- [ ] 0.4 **En Manus workspace:** activar HubSpot connector (aceptar la solicitud de autorización).
      Verificar que Gmail está habilitado y Meta Ads está configurado. Confirmar que la API de
      Tareas `/sell-machine/tasks/recent` devuelve datos.

---

## Fase A — Jarvis Personal por Telegram (un solo bot, D1)

- [x] 1. Crear `apps/backend/presentation/jarvis_endpoints.py` — webhook handler + chat proxy +
      brief endpoint (commit `45fd4af`, 2026-09-13 o antes) — **el webhook standalone se elimina
      en la tarea 1.4 de abajo; `/jarvis/chat`, `/jarvis/status`, `/jarvis/brief` se conservan**
- [x] 2. Registrar router de Jarvis en `apps/backend/presentation/router.py` (commit `45fd4af`)
      — **el registro del `webhook_router` de Jarvis se retira en la tarea 1.4**
- [x] 3. Actualizar `apps/backend/config.py` — agregar env vars (commit `45fd4af`) — **
      `TELEGRAM_BOT_TOKEN_JARVIS`/`TELEGRAM_WEBHOOK_SECRET_JARVIS` se eliminan en la tarea 1.4;
      `TELEGRAM_JUAN_DAVID_CHAT_ID` se conserva**
- [ ] 1.1 Test que falla: un update con `chat.id == TELEGRAM_JUAN_DAVID_CHAT_ID` en el webhook de
      **Taty** (`telegram_endpoints.py`) se enruta a Hermes (mock de `resolve_hermes_gateway_url`
      y del `POST /api/run`, no del handler) y **no** consulta `telegram_chat_mappings`
- [ ] 1.2 Test que falla: un `chat_id` distinto sigue el flujo actual (mappings → Taty) sin
      cambios — contrato aditivo, byte-idéntico
- [ ] 1.3 Mover la lógica del webhook Jarvis (system prompt admin, timeout 55s, mensajes de
      error) a `telegram_endpoints.py` como rama previa al lookup de mappings. Enviar la
      respuesta con el mismo `send_telegram_message()` y `TELEGRAM_BOT_TOKEN`
- [ ] 1.4 Eliminar `webhook_router` de `jarvis_endpoints.py` y su registro en `router.py`;
      eliminar `TELEGRAM_BOT_TOKEN_JARVIS` y `TELEGRAM_WEBHOOK_SECRET_JARVIS` de `config.py` y de
      `jarvis_endpoints.py`. Conservar `TELEGRAM_JUAN_DAVID_CHAT_ID`
- [ ] 1.5 **Hallazgo a corregir de paso** (mismo change): `telegram_endpoints.py` tiene la
      verificación de firma del webhook desactivada (TODO). Activar verificación con
      `X-Telegram-Bot-Api-Secret-Token` usando `TELEGRAM_WEBHOOK_SECRET` (patrón ya escrito en
      `jarvis_endpoints.py::_verify_jarvis_webhook_secret`). Test: secreto incorrecto → 200 sin
      acción (Telegram reintenta en 4xx, nunca en 200)
- [ ] 1.6 Skill Hermes `jarvis-personal.md` en
      `C:\Users\contexia\AppData\Local\hermes\profiles\contexia\skills\` (canónica en
      `ai-specs/skills/`, desplegada vía `scripts/sync_hermes_skills.ps1` — añadir a
      `$CanonicalSkills`)
- [ ] 1.7 Founder: obtener `TELEGRAM_JUAN_DAVID_CHAT_ID` y setearlo en Railway (mismo que 0.2)
- [ ] 7. Crear cron Hermes `jarvis-morning-brief.sh` + registrar en `jobs.json` (9:00 AM COT):
  - [ ] 7a. Confirmar Stage 0.4 completado (HubSpot activado en Manus, Gmail/Meta listos)
  - [ ] 7b. Implementar llamada al backend Railway (`POST /api/v1/jarvis/brief`) para contexto
        financiero (Caja Real + alertas + Approval Queue)
  - [ ] 7c. Implementar llamada a Manus (`GET /sell-machine/tasks/recent?hours=24`) para contexto
        comercial — fail-graceful: si Manus no responde, omite sección sin fallar
  - [ ] 7d. Hermes agrega ambos payloads y redacta el brief unificado → envía a
        `TELEGRAM_JUAN_DAVID_CHAT_ID`
- [ ] 8. Smoke test Fase A: mensaje al bot de Taty desde el `chat_id` del fundador → respuesta de
      Hermes visible en Telegram; mensaje desde otro `chat_id` → flujo Taty normal, sin regresión

---

## Fase B — Búnker Agentic OS (D6: mismo `jarvis-client.ts` que la burbuja PWA)

> **Reconciliación 2026-09-13:** esta fase ya estaba COMPLETA en `main` (commit `4933f0a`,
> 2026-09-02) — el HANDOFF.md de este hilo decía "no construida", desactualizado. Verificado en
> disco antes de re-implementar nada.

- [x] 9. `contexia-app/components/bunker/agentic-os/` — 5 archivos: `AgenticOsSection.tsx`
      (feature-gating por plan_tier/rol admin, JWT), `HermesStatusCard.tsx`, `JarvisChatInterface.tsx`
      (SSE streaming), `VoiceToggle.tsx` (Web Speech API), `CronJobsMonitor.tsx` (admin-only)
      — commit `4933f0a`
- [x] 10. `contexia-app/lib/jarvis-client.ts` — commit `4933f0a`. **Bug real encontrado y
      corregido 2026-09-13** (este hilo): `HermesStatusResponse` esperaba
      `{online, url, uptime_seconds}` pero el backend (`jarvis_endpoints.py::jarvis_status`)
      siempre devuelve `{status, gateway_url, hermes}` — `HermesStatusCard` mostraba "Sin
      conexión" incluso con Hermes sano, porque `res.online` era `undefined`. Corregido el tipo
      y el mapeo en `HermesStatusCard.tsx`. También se eliminó `chat()` (dead code: `/jarvis/chat`
      es SSE-only, `.json()` sobre ese stream siempre habría lanzado — `JarvisChatInterface`
      hace su propio `fetch()`/`getReader()`, nunca llamó a este método)
- [x] 11. `contexia-app/lib/config.ts` ya tenía `jarvisChat`/`jarvisStatus`/`JARVIS_CHAT_URL`/
      `JARVIS_STATUS_URL` — commit `4933f0a`
- [x] 12. `contexia-app/app/app/bunker/page.tsx` ya tenía `AgenticOsSection` importado y
      `"agentic-os"` fuera de `PLACEHOLDER_SECTIONS` — commit `4933f0a`

---

## Fase C — Tier display y feature gating

- [x] 13. Actualizar `apps/backend/core/plan_features.py` — agregar `jarvis_chat` (growth+),
      `jarvis_voice` (enterprise) — adoptado del working tree 2026-09-13, commit `666495b`
- [x] 14. Actualizar `contexia-app/components/config/TenantInfoCard.tsx` — display names por
      tier, corregidos 2026-09-13 (commit `666495b`) para coincidir exactamente con
      `pricing_catalog.py::SOFTWARE_TIERS` (Pulso/GPS/Contexia Pro/Contexia Total) — la versión
      original confundía freemium y starter bajo el mismo label "Pulso Básico"
- [x] 15. Actualizar `contexia-app/components/shared/UpgradePlanBanner.tsx` — copy con pricing
      real, corregido 2026-09-13 (commit `666495b`) — el texto original decía "Disponible desde
      Pulso Básico Growth" (dos nombres de tier concatenados)

---

## Fase D — Jarvis para clientes B2B vía WhatsApp (D2, generaliza la Fase D original)

- [ ] 16. En la ruta de respuesta de WhatsApp (`taty_lead_router.py` / `whatsapp_endpoints.py`):
      si el tenant del lead tiene `plan_tier ∈ {growth, enterprise}` → proxy a Hermes (contexto
      del tenant, vía el mismo mecanismo que `/jarvis/chat`); si no → Taty básica sin cambios
- [ ] 17. Test: un lead `plan_tier=freemium/starter` no cambia de comportamiento (contrato
      aditivo, byte-idéntico); un lead `growth/enterprise` recibe respuesta vía Hermes
- [ ] 18. Gate por `has_feature(plan_tier, "jarvis_chat")` (mismo helper de Fase B/C, sin
      duplicar lógica de gating)

---

## Fase E — Burbuja Jarvis en el PWA (D4/D5, nuevo — no existía en el proposal original)

- [ ] 19. Burbuja flotante en `contexia-app/app/app/(shell)/layout.tsx` (un solo punto que
      envuelve overview/fiscal/flujo-detalle/patrimonio/radar) — **no** un quinto ícono en
      `BottomNav.tsx`
- [ ] 20. Mini-visualizer con estados `escuchando / pensando / respondiendo` (D5 — NO la versión
      de pantalla completa)
- [ ] 21. Reusa `jarvis-client.ts` (mismo cliente de la Fase B) y el gate `jarvis_chat`/`jarvis_voice`

---

## Stage 11. Deploy a producción (OBLIGATORIO)

Ver: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 11.1 git commit + push to main (requiere confirmación explícita del fundador)
- [ ] 11.2 Vercel build completo (verde ✅)
- [ ] 11.3 Railway deploy activo (backend cambió)
- [ ] 11.4 URLs de producción: Jarvis responde en Telegram (bot único de Taty) + Agentic OS
      visible en el Búnker + burbuja visible en el PWA (gated por plan)
- [ ] 11.5 Crear reporte: `openspec/changes/hermes-jarvis-contexia/reports/YYYY-MM-DD-deployment.md`
