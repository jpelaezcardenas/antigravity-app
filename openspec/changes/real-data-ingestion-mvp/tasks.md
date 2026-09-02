# Tasks: real-data-ingestion-mvp

**Change:** real-data-ingestion-mvp
**Status:** apply

---

## Prerequisito 0 — Fix auth en shadow_gl_endpoints

- [x] 0.1 Agregar `Depends(get_current_user)` a los 3 endpoints POST
- [x] 0.2 Reemplazar `_resolve_tenant_id()` por `resolve_request_tenant_scope()` en los 3 endpoints
- [x] 0.3 Agregar alias `POST /api/v1/shadow-gl/upload` que acepta cualquier formato
- [ ] 0.4 Actualizar tests en `test_shadow_gl_endpoints.py`

---

## Track 4 — Multi-format Parser (compartido por todos los tracks)

- [ ] 4.1 Agregar `openpyxl==3.1.2` y `pypdf==4.3.1` a `apps/backend/requirements.txt`
- [ ] 4.2 Crear `apps/backend/services/multi_format_parser.py` con `parse_any_to_siigo_rows()`
- [ ] 4.3 Crear `apps/backend/tests/test_multi_format_parser.py` (TDD: CSV, Excel, PDF-XML, PDF-texto, formato inválido)

---

## Track 1 — PWA Upload Self-Service

- [ ] 1.1 Crear `contexia-app/lib/ingestion-api.ts`
- [ ] 1.2 Actualizar `contexia-app/lib/config.ts` — agregar `UPLOAD_DATA` endpoint
- [ ] 1.3 Crear `contexia-app/components/pulso/DataUploadCard.tsx`
- [ ] 1.4 Actualizar `contexia-app/app/app/(shell)/overview/page.tsx` — agregar DataUploadCard
- [ ] 1.5 Build check: `npm run build` desde `contexia-app/`

---

## Track 2 — Siigo API Key Sync

- [ ] 2.1 Crear `apps/backend/services/siigo_api_client.py`
- [ ] 2.2 Crear `apps/backend/presentation/siigo_sync_endpoints.py` — `POST /internal/siigo-sync/run`
- [ ] 2.3 Registrar router en `apps/backend/presentation/router.py`
- [ ] 2.4 Crear `apps/hermes-siigo-poller/` (patrón hubspot-poller)
- [ ] 2.5 Tests: `pytest -k siigo_api_client --dry-run` con sandbox

---

## Track 3 — Gmail Adjuntos Ingest

- [ ] 3.1 Crear migration `0048_gmail_sender_map.sql`
- [ ] 3.2 Crear `apps/backend/presentation/ingest_file_endpoints.py` — `POST /internal/ingest/file`
- [ ] 3.3 Registrar router en `apps/backend/presentation/router.py`
- [ ] 3.4 Crear `apps/hermes-gmail-poller/` (patrón hubspot-poller)
- [ ] 3.5 Registrar tarea en Windows Task Scheduler

---

## Stage 11. Deploy a producción (OBLIGATORIO)

- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build completo (verde ✅)
- [ ] 11.3 Railway deploy activo
- [ ] 11.4 Verificar: subir CSV desde `/app/overview` → datos visibles en Supabase con `is_verified_real=true`
- [ ] 11.5 Crear reporte: `openspec/changes/real-data-ingestion-mvp/reports/YYYY-MM-DD-deployment.md`
