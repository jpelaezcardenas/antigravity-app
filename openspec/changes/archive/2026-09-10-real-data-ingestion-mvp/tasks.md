# Tasks: real-data-ingestion-mvp

**Change:** real-data-ingestion-mvp
**Status:** apply

---

## Prerequisito 0 — Fix auth en shadow_gl_endpoints

- [x] 0.1 Agregar `Depends(get_current_user)` a los 3 endpoints POST
- [x] 0.2 Reemplazar `_resolve_tenant_id()` por `resolve_request_tenant_scope()` en los 3 endpoints
- [x] 0.3 Agregar alias `POST /api/v1/shadow-gl/upload` que acepta cualquier formato
- [x] 0.4 Actualizar tests en `test_shadow_gl_endpoints.py` — 9/9 passed

---

## Track 4 — Multi-format Parser (compartido por todos los tracks)

- [x] 4.1 Agregar `openpyxl==3.1.2` y `pypdf==4.3.1` a `apps/backend/requirements.txt`
- [x] 4.2 Crear `apps/backend/services/multi_format_parser.py` con `parse_any_to_siigo_rows()`
- [x] 4.3 Crear `apps/backend/tests/test_multi_format_parser.py` (TDD: CSV, Excel, PDF-XML, PDF-texto, formato inválido) — 8/8 passed

---

## Track 1 — PWA Upload Self-Service

- [x] 1.1 Crear `contexia-app/lib/ingestion-api.ts`
- [x] 1.2 Actualizar `contexia-app/lib/config.ts` — agregar `uploadData` endpoint
- [x] 1.3 Crear `contexia-app/components/pulso/DataUploadCard.tsx`
- [x] 1.4 Actualizar `contexia-app/app/app/(shell)/overview/page.tsx` — agregar DataUploadCard
- [x] 1.5 Build check: compilado con éxito (Next.js 21s)

---

## Track 2 — Siigo API Key Sync (BLOQUEADO 2026-09-09, no por falta de código)

**Bloqueo real, no técnico:** requiere `SIIGO_PARTNER_ID`, obtenido del consola de partners de
Siigo — Contexia confirmó que **no es partner de Siigo** hoy. Sin eso, ningún cliente puede
sincronizar vía este track, sin importar cuántas credenciales `SIIGO_USERNAME_<tenant>`/
`SIIGO_ACCESS_KEY_<tenant>` se configuren. El código sigue correcto y fail-closed (D6 del
`design.md`: nunca adivina el Partner-Id). **Decisión del fundador (2026-09-09): pausar este
track indefinidamente** — el foco pasa a B2C (declaración de renta persona natural, temporada
actual), donde la ingesta real ya es manual (ver Track 1 y `taty-document-collection`, no Siigo).
Retomar solo si Contexia se registra como partner de Siigo en el futuro.



- [x] 2.1 Crear `apps/backend/services/siigo_api_client.py`
- [x] 2.2 Crear `apps/backend/presentation/siigo_sync_endpoints.py` — `POST /internal/siigo-sync/run`
- [x] 2.3 Registrar router en `apps/backend/main.py` (prefix `/internal`, fuera de api/v1)
- [x] 2.4 Crear `apps/hermes-siigo-poller/` (patrón hubspot-poller, nightly 2 AM)
- [x] 2.5 Tests: `pytest tests/test_siigo_api_client.py` — 11/11 passed

---

## Track 3 — Gmail Adjuntos Ingest (PAUSADO 2026-09-09, sin bloqueo técnico)

**Decisión del fundador (2026-09-09):** no se va a definir todavía el correo de Taty
(`GMAIL_INBOX_ADDRESS`) — se avanza sin esto. La tarea programada `ContexiaHermesGmailPoller` ya
quedó registrada (3.5) y corre cada 15 min, pero se queda inerte hasta que exista `.env` +
`credentials.json` (fail-closed por diseño, no genera efectos secundarios). Para B2C, el canal
real de recepción de documentos ya es WhatsApp directo a Taty
(`taty-document-collection`, ya archivado y en producción) — Gmail queda como puerta B2B/futura,
sin urgencia mientras el foco es la temporada de Renta Natural.



- [x] 3.1 Crear migration `0046_gmail_sender_map.sql` (numeración corregida: 0046, no 0048)
- [x] 3.1b Corregir bug real en la política RLS `gmail_sender_map_tenant_read` (línea 36): referenciaba
      `resolved_tenant_id`, columna inexistente en `user_tenants` (la columna real es `tenant_id`,
      confirmado contra `0004_user_tenants_table.sql`). Sin este fix, la migración habría fallado al
      aplicarse. Corregido 2026-09-09, no aplicado todavía en Supabase (tarea 3.6).
- [x] 3.2 Crear `apps/backend/presentation/ingest_file_endpoints.py` — `POST /internal/ingest/file`
- [x] 3.3 Registrar router en `apps/backend/main.py` (prefix `/internal`)
- [x] 3.4 Crear `apps/hermes-gmail-poller/` (patrón hubspot-poller, cada 15 min)
- [x] 3.5 Registrar tarea en Windows Task Scheduler — ambas tareas creadas y verificadas:
      `ContexiaHermesSiigoPoller` (diaria 2:00 AM) y `ContexiaHermesGmailPoller` (cada 15 min).
      **Bug real encontrado y corregido en el camino**: `hermes-siigo-poller/register_poller_task.ps1`
      usaba el operador `?.` (null-conditional), sintaxis exclusiva de PowerShell 7+ — fallaba con
      `powershell.exe` 5.1 (el que trae Windows por defecto, confirmado en este equipo). Corregido
      con el mismo patrón if/else que ya usaban los scripts de Gmail y HubSpot. Aparte de eso, el
      cmdlet `Register-ScheduledTask` (CIM) devolvió "Acceso denegado" en esta sesión — las tareas
      se registraron con `schtasks.exe` directamente (mismo resultado funcional: modo de inicio de
      sesión "Solo interactivo", equivalente al trigger `AtLogOn` de los scripts), envolviendo el
      comando en `cmd /c cd /d <dir> && pythonw.exe main.py` porque `config.py` carga `.env` con
      ruta relativa (`env_file=".env"`, resuelta contra el directorio de trabajo del proceso, no
      contra la ubicación del script) — Task Scheduler por defecto arranca en `System32` si no se
      fija el directorio de inicio.
- [x] 3.6 Aplicar migration `0046` en Supabase — aplicada 2026-09-09, con confirmación explícita
      del fundador. Verificada en vivo: tabla `gmail_sender_map` existe, ambas políticas RLS
      (`gmail_sender_map_service_all`, `gmail_sender_map_tenant_read`) creadas sin error.
- [ ] 3.7 OAuth2 Gmail: descargar `credentials.json` de Google Cloud Console — **acción manual del
      fundador, requiere flujo interactivo de navegador y manejo de credenciales; no delegable**

---

## Stage 11. Deploy a producción (OBLIGATORIO)

- [x] 11.1 git commit + push to main (múltiples commits: fix migración 0046, registro de tareas
      programadas, migración 0050 `ingestion_batches`).
- [x] 11.2 Vercel: `DataUploadCard` ya en producción (no requirió cambio de frontend para el fix).
- [x] 11.3 Railway deploy activo — verificado.
- [x] 11.4 **Verificado con archivo real de CÓDIGO 520 desde `/app/overview`**: bug real
      encontrado en el camino — `ingestion_batches` no existía (migración 0019 tenía 3 errores de
      sintaxis Postgres que la hacían fallar silenciosamente desde siempre; ver migración `0050`).
      Corregido, aplicado, y confirmado con la subida real del fundador: `erp_journal_entries` id
      `4ff7384a-d8d0-4c21-8573-5cbd3da68eb8`, `source="siigo_csv"`, `is_verified_real=true`,
      `tenant_id` de CÓDIGO 520 (no Cliente Cero) — contra un baseline capturado antes en 0
      registros reales.
- [x] 11.5 Reporte: ver `openspec/changes/real-data-ingestion-mvp/reports/2026-09-10-deployment.md`.
