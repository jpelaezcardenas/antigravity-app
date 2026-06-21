# Bunker Social Content Ops - Retoma 2026-05-28

## Objetivo
Retomar el trabajo del Bunker para dejar `/app/bunker` como centro operativo 5.0 de Contexia: adquisicion inbound, marketing organico, onboarding 21D, service desk, ventas/leads/cierre y human-in-the-loop.

## Contexto
Contexia necesita que el Bunker conserve la estetica actual del Admin live: sidebar izquierda, topbar con busqueda, colores oscuros/cyan y navegacion de Operaciones. La nueva version no debe depender del backend caido `contexia-content-os` ni de workflows n8n para las funciones criticas de Social Media Ops.

## Estado Actual Del Repo
El working tree esta dirty. Hay cambios relevantes del Bunker/Social Ops y tambien cambios no relacionados que no deben revertirse sin revision:

- Cambios Social Ops/Bunker:
  - `apps/backend/services/social_ops_service.py`
  - `apps/backend/presentation/social_ops_endpoints.py`
  - `apps/backend/presentation/router.py`
  - `apps/backend/presentation/telegram_endpoints.py`
  - `frontend/dashboard/src/BunkerApp.tsx`
  - `frontend/dashboard/src/components/layout/AdminShell.tsx`
  - `frontend/dashboard/src/components/ops/SocialContentOps.tsx`
  - `frontend/dashboard/src/components/ops/IdeasOps.tsx`
  - `frontend/dashboard/src/components/ops/MetricasDashboard.tsx`
  - `app/bunker/index.html`
  - `vercel.json`

- Eliminaciones intencionales del modulo viejo:
  - `frontend/dashboard/src/components/ops/IdeasKanban.tsx`
  - `frontend/dashboard/src/components/ops/SocialMediaOps.tsx`

- Cambios/archivos no relacionados detectados:
  - `docs/auth-routing.md`
  - `docs/runbooks/INCIDENT-001-PWA-PERDIDA.md`
  - `docs/runbooks/auth-routing.md`
  - `docs/shadow-audit-knowledge-base.md`
  - varios archivos nuevos en `.agent/`, `.antigravity/`, `.claude/`, `.codex/`, `ai-specs/`, `openspec/`

## Arquitectura Implementada

### Backend Core Unificado
Los endpoints nuevos viven bajo `/api/v1/social-ops` y reemplazan la dependencia directa al Content OS caido.

- Inbox y pipeline:
  - `GET /api/v1/social-ops/inbox`
  - `GET /api/v1/social-ops/pipeline`
  - `POST /api/v1/social-ops/events/simulate`
  - `POST /api/v1/social-ops/diagnose`

- Comandos y aprobaciones:
  - `POST /api/v1/social-ops/commands/parse`
  - `GET /api/v1/social-ops/approvals`
  - `POST /api/v1/social-ops/approvals/{draft_type}/{draft_id}/approve`
  - `POST /api/v1/social-ops/approvals/{draft_type}/{draft_id}/reject`

- Onboarding 21D:
  - `GET /api/v1/social-ops/onboarding`
  - `POST /api/v1/social-ops/onboarding/start`
  - `POST /api/v1/social-ops/onboarding/{workspace_id}/intake`
  - `POST /api/v1/social-ops/onboarding/{workspace_id}/seed`
  - `POST /api/v1/social-ops/onboarding/{workspace_id}/steps/{step_id}/advance`

- Ventas/leads/cierre:
  - `POST /api/v1/social-ops/leads/reply-draft`
  - `POST /api/v1/social-ops/leads/sales-draft`

- Operaciones de contenido:
  - `GET /api/v1/social-ops/ideas`
  - `POST /api/v1/social-ops/ideas/{idea_id}/status`
  - `POST /api/v1/social-ops/ideas/{idea_id}/generate-draft`
  - `GET /api/v1/social-ops/metrics`
  - `POST /api/v1/social-ops/metrics/simulate`

- Canales:
  - `GET/POST /api/v1/channels/meta/webhook`
  - `POST /api/v1/channels/tiktok/webhook`
  - `POST /api/v1/channels/linkedin/sync`
  - Telegram extendido desde `apps/backend/presentation/telegram_endpoints.py`

### Taty Como Cara 24/7
Taty sigue siendo el frente conversacional. Telegram fiscal normal sigue usando Taty; si existe onboarding activo para una empresa, Taty captura datos de onboarding conversacionalmente. Los comandos y acciones sensibles quedan como drafts en `pending_approval`.

### Human-In-The-Loop
La Approval Queue es el punto obligatorio de aprobacion humana. Unifica:

- Comandos Zero-UI
- Seeds de onboarding
- Reply drafts de leads
- Sales drafts
- Service desk replies

### Operaciones Rescatadas
La pantalla Operaciones conserva:

- Ideas
- Calendario
- Borradores
- Metricas

Ideas y Metricas ya consumen FastAPI. Calendario y Borradores todavia deben revisarse para eliminar dependencia directa a Supabase/frontend si se quiere centralizar todo en backend.

## Checklist De Retoma

### 1. Validar Local
- Levantar backend:
  - `cd apps/backend`
  - `python -m uvicorn main:app --port 8080 --reload`
- Levantar frontend:
  - `cd frontend/dashboard`
  - `npm run dev`
- Abrir:
  - `http://localhost:5173/app/bunker/`

### 2. Smoke Tests UI
- Confirmar sidebar izquierda y topbar con busqueda.
- Entrar a Operaciones.
- Confirmar header "Social Media OPs Systems".
- Confirmar tabs de Operaciones: Ideas, Calendario, Borradores, Metricas.
- En Ideas:
  - seleccionar idea
  - generar IA
  - confirmar que llama FastAPI
- En Metricas:
  - ver estado vacio
  - click "Simular metricas"
  - confirmar tarjetas y tabla
- En Inbox:
  - simular evento inbound
  - confirmar lead en pipeline
- En Pipeline:
  - generar draft de cierre
- En Aprobaciones:
  - aprobar/rechazar draft
- En Onboarding:
  - iniciar onboarding
  - analizar intake sin formularios

### 3. Validar API
- `GET http://localhost:8080/api/v1/social-ops/pipeline`
- `GET http://localhost:8080/api/v1/social-ops/ideas`
- `GET http://localhost:8080/api/v1/social-ops/metrics`
- `POST http://localhost:8080/api/v1/social-ops/metrics/simulate`
- `GET http://localhost:8080/api/v1/social-ops/approvals`

### 4. Validar Build
- `cd frontend/dashboard`
- `npm run build`
- `cd ../..`
- `pytest -q apps/backend/tests/test_social_ops_service.py apps/backend/tests/test_social_ops_endpoints.py`

### 5. Preparar Live
- Confirmar que `vercel.json` enruta `/app/bunker` a `app/bunker/index.html`.
- Confirmar que `app/bunker/index.html` apunta a los assets actuales copiados desde `frontend/dashboard/dist/assets`.
- Confirmar que `/api/v1/:path*` reescribe al backend core Railway.

### 6. Limpieza Pendiente
- Revisar si los assets antiguos en `assets/index-*.js/css` se pueden borrar despues de validar produccion.
- Revisar eliminaciones de `docs/*` antes de commit.
- Revisar carpetas nuevas `.agent/`, `.antigravity/`, `.claude/`, `.codex/`, `ai-specs/`, `openspec/` antes de incluirlas.
- Consolidar Calendario y Borradores para que usen API backend en lugar de acceso directo desde frontend.

## Criterios De Aceptacion
- `/app/bunker` carga el shell Admin con sidebar y topbar.
- Operaciones conserva Ideas, Calendario, Borradores y Metricas.
- Ideas y Metricas funcionan via FastAPI.
- Taty puede manejar onboarding conversacional por Telegram cuando exista onboarding activo.
- Approval Queue opera como human-in-the-loop.
- No queda referencia activa a `contexia-content-os-production`.
- Build frontend OK.
- Tests backend Social Ops OK.

## Riesgos
- El repo esta dirty y contiene cambios no relacionados; antes de commit hay que separar cuidadosamente.
- `app/bunker/index.html` usa assets hasheados; cada build exige copiar assets nuevos y actualizar referencias.
- Persistencia Supabase esta preparada por migracion, pero el servicio puede caer a memoria si `SOCIAL_OPS_PERSIST_SUPABASE` no esta activo o las tablas no existen.
- Calendario/Borradores todavia pueden depender de Supabase desde frontend.

## Proximo Paso Recomendado
Primero validar local con backend y frontend vivos. Despues, migrar Calendario y Borradores a endpoints FastAPI para completar el rescate de Operaciones sin n8n ni acceso directo desde frontend.
