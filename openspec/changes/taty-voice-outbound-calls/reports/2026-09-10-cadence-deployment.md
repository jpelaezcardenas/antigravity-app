# Deployment report — taty-followup-cadence (Task 1 of taty-voice-outbound-calls)

**Fecha:** 2026-09-09/10
**Commit:** `73d5498`
**Scope:** solo la cadencia de seguimiento de 14 días (texto, WhatsApp). Las tareas 2-9
(Twilio/voz) no se tocaron — siguen bloqueadas, sin código nuevo.

## Qué se construyó

- `crm_leads.last_inbound_at` / `cadence_day` / `cadence_completed_at` — columnas aditivas,
  sin backfill.
- `POST /internal/cadence/send-touch` — mismo patrón `INTERNAL_API_KEY` fail-closed que cada
  endpoint `/internal/*` existente.
- `taty_lead_router.route_lead_message()` ahora estampa `last_inbound_at` y resetea
  `cadence_day` a `NULL` en cada mensaje entrante real — es lo que hace cierto que "un lead que
  responde sale de la cadencia automática".
- `apps/hermes-cadence-poller/` — nuevo poller local, corre cada hora, mismo esqueleto que los
  pollers de Siigo/Gmail/HubSpot ya existentes.

## Stage 11 — checklist

- [x] Migración `0051` aplicada en Supabase (confirmación explícita), verificada en vivo:
  `last_inbound_at timestamptz`, `cadence_day integer`, `cadence_completed_at timestamptz`,
  todas nullable, sin default.
- [x] Tarea programada `ContexiaHermesCadencePoller` registrada — el cmdlet
  `Register-ScheduledTask` (CIM) volvió a fallar con "Acceso denegado" en esta sesión, igual que
  con los pollers de Siigo/Gmail; se registró con `schtasks.exe` directo, mismo patrón que esas
  dos veces anteriores (`cmd /c cd /d <dir> && pythonw.exe main.py`, porque `config.py` carga
  `.env` relativo al directorio de trabajo).
- [x] `.env` del poller creado con las mismas credenciales que ya usan los otros pollers
  (`INTERNAL_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) — nunca commiteado, verificado
  contra `.gitignore`.
- [x] Dry-run ejecutado contra producción real: detectó correctamente 2 leads elegibles
  (día 14, sin respuesta), sin enviar nada (modo `--dry-run`).
- [x] git commit `73d5498` + push a `main`.
- [x] Railway deploy `71c80e02` → `SUCCESS`.
- [x] Verificación en vivo: `GET /api/v1/health` → `200`. `POST /internal/cadence/send-touch` con
  key incorrecta → `401` (montado, autenticación exigida, mismo comportamiento que todo otro
  endpoint `/internal/*`).

## Suites verificadas antes del push

- `apps/backend/tests/test_cadence_endpoint.py`, `test_cadence_schedule.py`,
  `test_taty_lead_router_cadence_reset.py`: **26/26 passed**.
- `apps/hermes-cadence-poller/`: **13/13 passed**.
- Sweep completo previo (implementer + reviewer, este mismo día): 86 + 62 (regresión) + 13, cero
  regresión contra `main`.

## Pendiente, no bloqueante

El poller corre cada hora; la primera ejecución real (no dry-run) todavía no se ha observado en
los logs — se recomienda revisar `apps/hermes-cadence-poller/logs/` (si aplica; confirmar que el
poller escribe logs a archivo, no solo a consola) después de la primera hora en producción real
para confirmar que un envío real de WhatsApp efectivamente sale.
