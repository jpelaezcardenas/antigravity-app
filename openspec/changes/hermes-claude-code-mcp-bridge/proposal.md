## Why

El fundador quiere adoptar el patrón "loop engineering" (Hermes orquesta, Claude Code construye,
conectados por MCP, con un loop que se auto-verifica contra tests) para seguir usando Claude Code
para desarrollo y Hermes para orquestación. Antes de construir el bridge nuevo, la exploración
inicial de este change encontró dos problemas de base que deben cerrarse primero: (1)
`docs/integrations/HERMES-SELF-CONFIG.md` contiene información fabricada (tres "roles" —
`centinela-monitor`, `auditoria-runner`, `resolucion-executor` — que no existen en ningún perfil,
bot o job real de Hermes) que viola la regla de CLAUDE.md §9 (nunca fabricar contenido sin fuente
real), y (2) el dashboard de Hermes muestra un job de producción (`Social Ops`) fallando con
`SESSION_NOT_OWNED` y un gateway sirviendo módulos desincronizados — construir un bridge nuevo
sobre un gateway que ya falla propagaría el mismo bug a cualquier delegación futura a Claude Code.

## What Changes

- **Purgar** de `docs/integrations/HERMES-SELF-CONFIG.md` toda referencia a los 3 roles fabricados
  (`centinela-monitor`, `auditoria-runner`, `resolucion-executor`) y reemplazarla por el mapeo real
  confirmado: 11 perfiles en disco (`/home/contexia/.hermes/profiles/`) ↔ 11 bots del Electron
  Desktop ↔ 9 agentes de `AGENTES.md`.
- **Diagnosticar y corregir** el bug `SESSION_NOT_OWNED` / "mixed sys.modules" que hoy causa
  `delivery_failed` en el job Social Ops y `error`/shutdown interrumpido en Pulso Diario.
- **Documentar** en `ARCHITECTURE.md` la topología real de Hermes: núcleo en WSL + app de
  escritorio Electron (Windows nativo) que conecta al backend de Contexia vía el gateway Railway
  (`-175a`), no directo a Supabase — dato confirmado por el fundador, ausente hoy en la doc.
  Documentar también por qué solo el perfil `contexia` corre con gateway activo (123 skills)
  mientras los otros 10 perfiles muestran "Gateway stopped" — confirmar si es diseño esperado o
  síntoma del mismo bug de gateway.
- Este change **no** construye todavía el bridge MCP Hermes→Claude Code ni el loop de auto-fix
  (eso es un change posterior, una vez esta base esté sana y correctamente documentada).

## Capabilities

### New Capabilities
- `hermes-topology-docs`: documentación corregida y verificada de la topología real de Hermes
  (perfiles, bots, jobs, gateway, Electron Desktop) en `ARCHITECTURE.md` y
  `docs/integrations/HERMES-SELF-CONFIG.md`, sin contenido fabricado.

### Modified Capabilities
(ninguna — no existe ninguna capability de spec formal sobre Hermes hoy en `openspec/specs/`;
este change solo corrige documentación y un bug operativo de infraestructura, no contratos de API
del backend de Contexia.)

## Impact

- **Archivos de doc:** `docs/integrations/HERMES-SELF-CONFIG.md`, `ARCHITECTURE.md`, `AGENTES.md`
  (solo si la reconciliación de perfiles revela un desajuste real, hoy no esperado).
- **Infraestructura Hermes (fuera de este repo, en WSL/Windows local):** posible `hermes update`,
  `hermes gateway restart`, y cierre de la sesión con lease huérfano — acciones operativas del
  fundador, no cambios de código en `antigravity-app`.
- **Sin impacto en producción de Contexia** (Railway/Vercel/Supabase) — este change es
  exclusivamente infraestructura local de Hermes + documentación.
- **No hay Stage 11 de deploy a Railway/Vercel en este change** — la "verificación en producción"
  aquí es que los 8 Scheduled Jobs de Hermes corran sin error en su próximo ciclo.
