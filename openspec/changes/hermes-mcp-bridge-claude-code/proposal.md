## Why

El fundador quiere adoptar el patrón "loop engineering" (Hermes orquesta, Claude Code construye,
conectados por MCP) para que Claude Code pueda leer el estado de Hermes (canales, memoria,
cron jobs) desde este mismo repo, y para pilotar un primer loop determinista de auto-fix sobre
uno de los 8 Scheduled Jobs reales. El change previo (`hermes-claude-code-mcp-bridge`) cerró la
base necesaria: purgó documentación con afirmaciones falsas sobre el runtime de Hermes, resolvió
un bug real de gateway, y documentó la topología verificada (10 perfiles, 8 Scheduled Jobs,
Hermes Desktop vía gateway Railway). Ese change dejó explícitamente el bridge MCP en sí fuera de
alcance ("no se construye todavía... es un change posterior, una vez esta base esté sana"). Esta
propuesta es ese change posterior.

## What Changes

- Registrar Hermes como servidor MCP **project-scoped** en `antigravity-app/.mcp.json`, vía
  `hermes mcp serve` (subcomando real y verificado, corre sobre stdio, sin flags obligatorios).
- Verificar la conexión con `claude mcp list` / pidiendo a Claude Code que liste las tools de
  Hermes disponibles.
- **No** se construye un loop de auto-fix automático en este change — la Decisión #7 de
  `HARNESS.md`/`AGENTES.md` (Hermes nunca commitea/pushea a `antigravity-app` sin aprobación) y
  la ausencia de un gate de verificación ya probado para un piloto real hacen prematuro
  automatizar delegación sin supervisión. Este change se limita a **la conexión** (Fase 2 del
  plan original); un loop piloto es una fase posterior explícita, solo si el fundador decide
  seguir después de validar el bridge manualmente.

## Capabilities

### New Capabilities
- `hermes-mcp-bridge`: conexión MCP registrada de Hermes hacia Claude Code, scoped al proyecto,
  sin exponer datos de tenant ni credenciales de producción — solo orquestación de desarrollo.

### Modified Capabilities
(ninguna — no existe ninguna spec de API/backend de Contexia afectada; este change es
exclusivamente configuración de herramientas de desarrollo local.)

## Impact

- **Archivo nuevo:** `antigravity-app/.mcp.json` (project-scoped, no global — para no afectar
  otros repos del ecosistema).
- **Sin impacto en producción** (Railway/Vercel/Supabase) — es tooling de desarrollo local.
- **Sin Stage 11** — no hay deploy a Railway/Vercel en este change.
- **Alcance de seguridad explícito:** el bridge conecta Hermes (que sí tiene acceso a datos
  operativos locales — canales, memoria, cron) a Claude Code dentro de esta sesión de desarrollo.
  Ningún dato de tenant/Shadow GL debe fluir por este canal — es orquestación de tareas de
  código, no de negocio.
