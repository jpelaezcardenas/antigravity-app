## Context

`docs/integrations/HERMES-SELF-CONFIG.md` §6 documenta el gap explícitamente: "No existe un canal
directo bidireccional Hermes ↔ Claude Code. La coordinación hoy es... `COORDINATION-LOG.md` en
WSL" (manual). El sentido inverso ya existe: Claude Code lee el backend de Contexia vía 4 MCP
tools en `contexia_agents/server.py`. Lo que falta es que Claude Code pueda consultar Hermes
directamente (canales, memoria, cron) desde una sesión de desarrollo en este repo.

El change previo (`hermes-claude-code-mcp-bridge`) verificó en vivo que:
- `hermes mcp serve` es un subcomando real (`hermes mcp --help` lo confirma: "Run Hermes as an
  MCP server (expose conversations to other agents)"), sin flags obligatorios, corre sobre stdio.
- El gateway de Hermes (perfil `contexia`) está sano tras el fix de esa sesión.
- Existen 8 Scheduled Jobs reales que podrían servir de candidato a un loop piloto futuro, pero
  2 de ellos (Pulso Diario, Social Ops) tienen problemas activos NO relacionados con el bridge
  (ver ese change, tareas 2.4/3) — no son buenos candidatos para un piloto de auto-fix todavía,
  porque un loop de auto-fix necesita un gate limpio para poder medir éxito/fracaso con confianza.

## Goals / Non-Goals

**Goals:**
- Registrar el bridge MCP Hermes→Claude Code, project-scoped, y verificar la conexión.
- Dejar documentado en `ARCHITECTURE.md`/`HERMES-SELF-CONFIG.md` que el gap de §6 está cerrado.

**Non-Goals:**
- **No se construye el loop de auto-fix en este change.** Motivos: (1) HARNESS.md/AGENTES.md
  establecen que Hermes nunca commitea/pushea sin aprobación explícita — un loop que delega a
  Claude Code en modo no-interactivo y potencialmente hace commits automáticos necesita ese
  diseño de aprobación resuelto primero, no improvisado; (2) los 2 candidatos más obvios de job
  (Pulso Diario, Social Ops) tienen fallas activas de causa ya identificada pero no arreglada —
  usarlos de piloto mezclaría "el loop no funciona" con "el job ya fallaba por otra razón",
  imposible de diagnosticar limpiamente.
- No se toca ningún dato de tenant, Shadow GL, ni router `/api/v1/*` de Contexia.
- No se activa el cron nativo de Hermes para nada nuevo — ya está en uso (8 jobs reales).

## Decisions

**D1 — Scope MCP project-level, no global.**
`antigravity-app/.mcp.json` (no `~/.claude/mcp.json`) para que el bridge solo esté activo cuando
se trabaja en este repo — evita que otros proyectos del ecosistema (`contexia-brain`,
`contexia-ops-template`, etc.) hereden una dependencia de Hermes corriendo en WSL sin necesitarla.

**D2 — Bridge de solo lectura/orquestación de desarrollo, nunca de datos de negocio.**
El propósito declarado es que Claude Code pueda consultar el estado de Hermes (canales, cron,
memoria) para tareas de desarrollo — no un canal para que Hermes opere sobre Shadow GL o
approval_queue. Esa superficie ya existe, separada y ya autenticada, vía los 4 MCP tools de
`contexia_agents/server.py` en sentido inverso.

**D3 — Piloto de loop diferido a un change futuro explícito, no "mientras tanto".**
Alternativa considerada: usar Radar Predictivo (el único de los 3 jobs `bot-chat` que corrió
limpio ambos días verificados) como candidato de piloto ahora mismo. Se descarta por ahora:
validar primero que el bridge en sí funciona de forma aislada (sin nada más corriendo sobre él)
reduce las variables si algo falla la primera vez.

## Risks / Trade-offs

- **[Riesgo] `hermes mcp serve` podría fallar silenciosamente si el gateway del perfil `contexia`
  se cae mientras Claude Code lo tiene registrado** → **Mitigación:** verificar con `claude mcp
  list` inmediatamente después de registrar, y no asumir éxito solo por la ausencia de error al
  escribir `.mcp.json`.
- **[Riesgo] Confundir este bridge con un canal de datos de producción** → **Mitigación:** D2 —
  documentarlo explícitamente como bridge de desarrollo, nunca de negocio, en el propio
  `.mcp.json` (comentario) y en `ARCHITECTURE.md`.
- **[Trade-off] No resolver el loop de auto-fix ahora significa que el "resultado visible" de
  este change es solo conectividad, no automatización** → aceptado: es la secuencia correcta
  dado que los 2 jobs más obvios de pilotar tienen fallas activas no relacionadas (ver Context).

## Migration Plan

No hay migración de datos. Rollback trivial: eliminar la entrada de `antigravity-app/.mcp.json`.
Sin Stage 11 (no hay deploy a Railway/Vercel).

## Open Questions

- ¿Qué job usar como piloto de loop de auto-fix, una vez el bridge esté validado? Candidato
  preliminar: Radar Predictivo (único de los 3 `bot-chat` sin fallas activas), pero decisión del
  fundador en un change futuro, no aquí.
