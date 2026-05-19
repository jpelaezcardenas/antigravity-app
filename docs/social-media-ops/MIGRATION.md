# Migración Social Media OPs → antigravity-app

**Fecha:** 2026-05-19
**Branch:** `claude/laughing-knuth-16166d`
**Origen:** `C:\Users\contexia\Projects\Social Media OPs Systems`
**Destino:** `antigravity-app` (este repositorio)

## Por qué

Centralizar el Content OS dentro de `antigravity-app` para:

- Compartir base de datos (Supabase) y endpoint de inferencia (`/api/v1/llm/analyze`) con el backend FastAPI ya existente.
- Heredar autenticación y MFA del portal base (Búnker Contexia) sin reescribir seguridad.
- Eliminar duplicidad de variables de entorno, CORS y configuración.
- Mantener un único control de versiones.

## Mapa de la migración

| Origen (`Social Media OPs Systems/`)      | Destino (`antigravity-app/`)                  | Propósito                                              |
| ----------------------------------------- | --------------------------------------------- | ------------------------------------------------------ |
| `workflows/WF-*.json` (7 archivos)        | `.agents/workflows/`                          | Flujos n8n parametrizados (WF-01 a WF-10) — versionados |
| `rules.md`                                | `.agents/rules/rules.md`                      | Reglas globales canónicas (trigger: always_on)       |
| `OUTPUT_FORMAT.md`                        | `.agents/rules/OUTPUT_FORMAT.md`              | Esquema de salida JSON esperado de los prompts        |
| `Base de conocimientos-Contexia.md`       | `.agents/rules/Base de conocimientos-Contexia.md` | Knowledge base del ICP, dolores, voz y marca     |
| `PLAN.md`                                 | `docs/social-media-ops/PLAN.md`               | Plan maestro del Content OS                           |
| `README.md`                               | `docs/social-media-ops/README.md`             | Descripción general del Content OS                    |
| `DISCOVERY_TEMPLATE.md`                   | `docs/social-media-ops/DISCOVERY_TEMPLATE.md` | Plantilla de discovery respondida (documentación)     |
| `PROJECT_BRIEF.md`                        | `docs/social-media-ops/PROJECT_BRIEF.md`      | Brief estratégico del proyecto (documentación)        |
| `docs/decisions/*.md`                     | `docs/social-media-ops/decisions/`            | ADRs (Architecture Decision Records)                  |
| `docs/runbooks/*.md`                      | `docs/social-media-ops/runbooks/`             | Runbooks operativos (ej: Meta API setup)             |
| `docs/specs/*.md` (10 archivos)           | `docs/social-media-ops/specs/`                | Bloques 1-9 + roadmap                                 |
| `docs/specs/supabase-schema.sql`          | `docs/social-media-ops/specs/supabase-schema.sql` | Schema SQL (referencia — ya aplicado en Supabase) |

## Convención de carpetas adoptada

- **`.agents/`** → Insumos que consume Claude Code y los workflows automáticos (n8n).
  - `workflows/` → JSONs de n8n importables directamente.
  - `rules/` → Reglas de prompting, knowledge base y formatos de salida.
- **`docs/social-media-ops/`** → Documentación humana del subsistema (specs, ADRs, runbooks).

## Estado actual: Fase 1 — Fusión Física ✅

Los archivos físicos ya están dentro de `antigravity-app` con la organización final. Falta:

- **Fase 2:** Setup de Claude Code en la raíz del repo (instalar y loguear).
- **Fase 3:** QA del endpoint `/api/v1/llm/analyze` con los workflows de n8n apuntando al backend local.
- **Fase 4:** Construir la pestaña `/app/social-media-ops` dentro del Búnker (Next.js) reutilizando la auth del portal.

## Seguridad de keys

- `SUPABASE_SERVICE_ROLE_KEY` vive **únicamente** en:
  - El `.env` del backend FastAPI (en `apps/backend/`).
  - Las variables de entorno del servidor n8n.
- **Nunca** debe aparecer en el frontend (Next.js / HTML estático).
- En el frontend usar siempre `SUPABASE_ANON_KEY` + RLS.

## Protección de datos vivos

`.gitignore` bloquea automáticamente:

- `apps/backend/.env` — Credenciales Supabase del backend
- `.n8n/`, `n8n-data/`, `*.n8n.log` — Cache y logs de n8n (no subidos)
- `.agents/**/*.cache/`, `*.tmp`, `*.lock` — Archivos temporales

Los JSONs de workflows (`*.json`), reglas y documentación **SÍ se versionan** y suben al repo.

## Estrategia de publicación (MVP)

Publicación **semiautomática**: el sistema genera el borrador, dispara un correo Gmail con el link directo al Composer de Facebook, y un humano publica con un click. Esto evita pasar por el App Review de Meta durante el lanzamiento del MVP.

## Repositorio original

La carpeta `C:\Users\contexia\Projects\Social Media OPs Systems` se conserva como referencia. Una vez validada esta migración en QA (Fase 3), puede archivarse o eliminarse.
