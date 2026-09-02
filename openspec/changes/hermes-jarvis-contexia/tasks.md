# Tasks: hermes-jarvis-contexia

**Change:** hermes-jarvis-contexia
**Estado:** proposed (pendiente de design → spec → apply)

---

## Stage 0. Prerequisitos del fundador (no-código)

- [ ] 0.1 Crear bot nuevo en Telegram via @BotFather → guardar `TELEGRAM_BOT_TOKEN_JARVIS` en Bitwarden
- [ ] 0.2 Obtener `TELEGRAM_JUAN_DAVID_CHAT_ID` del chat personal
- [ ] 0.3 Confirmar que `tunnel_persistent.ps1` corre y que `hermes_tunnel[id='current']` tiene URL válida en Supabase

---

## Fase A — Jarvis Personal por Telegram

- [ ] 1. Crear `apps/backend/presentation/jarvis_endpoints.py` — webhook handler + chat proxy + brief endpoint
- [ ] 2. Registrar router de Jarvis en `apps/backend/presentation/router.py`
- [ ] 3. Actualizar `apps/backend/config.py` — agregar las 3 env vars nuevas
- [ ] 4. Setear env vars en Railway: `TELEGRAM_BOT_TOKEN_JARVIS`, `TELEGRAM_WEBHOOK_SECRET_JARVIS`, `TELEGRAM_JUAN_DAVID_CHAT_ID`
- [ ] 5. Registrar webhook de Telegram apuntando al endpoint de Railway
- [ ] 6. Crear skill `~/.hermes/profiles/contexia/skills/jarvis-personal.md`
- [ ] 7. Crear cron Hermes `jarvis-morning-brief.sh` + registrar en `jobs.json` (9:00 AM COT):
  - [ ] 7a. Confirmar con Manus el endpoint y shape del `GET /api/brief/context` (HubSpot pipeline + Gmail priority + Meta performance) — acción previa del fundador/Manus
  - [ ] 7b. Implementar llamada al backend Railway (`POST /api/v1/jarvis/brief`) para contexto financiero (Caja Real + alertas + Approval Queue)
  - [ ] 7c. Implementar llamada al API HTTP interno de Manus para contexto comercial (fail-graceful: si Manus no responde, omite sección sin fallar)
  - [ ] 7d. Hermes agrega ambos payloads y redacta el brief unificado → envía a `TELEGRAM_JUAN_DAVID_CHAT_ID`
- [ ] 8. Smoke test Fase A: mensaje al bot → respuesta de Hermes visible en Telegram

---

## Fase B — Búnker Agentic OS

- [ ] 9. Crear componentes `contexia-app/components/bunker/agentic-os/` (5 archivos)
- [ ] 10. Crear `contexia-app/lib/jarvis-client.ts`
- [ ] 11. Actualizar `contexia-app/lib/config.ts` — agregar endpoints JARVIS_CHAT y JARVIS_STATUS
- [ ] 12. Modificar `contexia-app/app/app/bunker/page.tsx` — quitar "agentic-os" de PLACEHOLDER_SECTIONS

---

## Fase C — Tier display y feature gating

- [ ] 13. Actualizar `apps/backend/core/plan_features.py` — agregar `jarvis_chat`, `jarvis_voice`; diferenciar starter vs growth vs enterprise
- [ ] 14. Actualizar `contexia-app/components/config/TenantInfoCard.tsx` — display names por tier
- [ ] 15. Actualizar `contexia-app/components/shared/UpgradePlanBanner.tsx` — copy con pricing real

---

## Stage 11. Deploy a producción (OBLIGATORIO)

Ver: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build completo (verde ✅)
- [ ] 11.3 Railway deploy activo (backend cambió)
- [ ] 11.4 URLs de producción: Jarvis responde en Telegram + Agentic OS visible en el Búnker
- [ ] 11.5 Crear reporte: `openspec/changes/hermes-jarvis-contexia/reports/YYYY-MM-DD-deployment.md`
