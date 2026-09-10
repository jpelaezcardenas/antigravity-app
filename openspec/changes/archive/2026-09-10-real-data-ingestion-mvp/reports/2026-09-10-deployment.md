# Deployment report — real-data-ingestion-mvp

**Fecha:** 2026-09-09/10
**Commits:** fix migración `0046` (`5356588`), registro de tareas programadas Siigo/Gmail
(`a1a2d26`), pausa de Tracks 2/3 por decisión de negocio (`5d270dd`), fix `ingestion_batches`
(`0788e3a`).

## Estado final por track

- **Track 1 (PWA upload)** — ✅ **Completo y verificado con datos reales.** Bug real encontrado:
  `ingestion_batches` nunca existió en producción — la migración `0019` que debía crearla tenía
  3 errores de sintaxis Postgres (`ADD COLUMN IF NOT EXISTS` con múltiples columnas agrupadas,
  `ADD CONSTRAINT ... UNIQUE (...) WHERE ...`, `CREATE POLICY IF NOT EXISTS`), así que fallaba
  completa y silenciosamente antes de llegar al `CREATE TABLE`. Migración `0050` la corrige
  (RLS permisiva, mismo patrón ya vivo en `erp_journal_entries`, no la política original basada
  en `user_roles.role_name` — columna que tampoco existe en producción). Verificado con la
  subida real del fundador desde CÓDIGO 520: `erp_journal_entries.is_verified_real=true`,
  `tenant_id` correcto, contra un baseline de 0 registros reales capturado antes de la prueba.
- **Track 2 (Siigo API sync)** — 🔴 **Pausado indefinidamente.** Contexia no es partner de Siigo;
  `SIIGO_PARTNER_ID` no se puede obtener. Bloqueo de negocio real, no técnico.
- **Track 3 (Gmail)** — 🟡 **Pausado por decisión.** Tareas programadas (`ContexiaHermesSiigoPoller`,
  `ContexiaHermesGmailPoller`) registradas y corriendo; migración `0046` (bug corregido) aplicada.
  Falta `GMAIL_INBOX_ADDRESS` + OAuth2 — decisión explícita del fundador de no definirlo aún.
- **Track 4 (parser multi-formato)** — ✅ Completo, es el que Track 1 usa en producción.

## Otro bug real encontrado en el camino (no de este change, corregido igual)

`apps/hermes-siigo-poller/register_poller_task.ps1` usaba el operador `?.` (PowerShell 7+), que
falla en `powershell.exe` 5.1 — el que trae Windows por defecto. Corregido con el mismo patrón
if/else que ya usaban los scripts de Gmail y HubSpot. Las tareas se registraron finalmente vía
`schtasks.exe` directo (el cmdlet `Register-ScheduledTask`/CIM devolvió "Acceso denegado" en esta
sesión), envolviendo el comando en `cmd /c cd /d <dir> && pythonw.exe main.py` porque `config.py`
carga `.env` con ruta relativa al directorio de trabajo, no al script.

## Pivote de prioridad de negocio (documentado, no oculto)

El fundador confirmó el foco en B2C (declaración de renta persona natural, temporada actual). La
ingesta real y prioritaria para esto **ya existe**: `taty-document-collection` (RUT/extractos por
WhatsApp, archivado dentro de `taty-whatsapp-renta-sales-capability`) — no depende de Siigo ni
Gmail. Track 1 de este change sigue vivo y sirve tanto a B2B (CÓDIGO 520) como a un futuro
autoservicio B2C.

## Conclusión

El change está funcionalmente completo para su prioridad real (Track 1, B2B self-service) y
documenta honestamente por qué los otros dos tracks quedan pausados sin fecha. Listo para
archivar.
