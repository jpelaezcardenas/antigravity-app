## ADDED Requirements

### Requirement: Bridge MCP Hermes registrado project-scoped
El repo `antigravity-app` SHALL registrar Hermes como servidor MCP en `.mcp.json` a nivel de
proyecto (no en la config global de Claude Code), invocando `hermes mcp serve`.

#### Scenario: Claude Code abre una sesión en antigravity-app
- **WHEN** se abre una sesión de Claude Code con working directory dentro de `antigravity-app`
- **THEN** el bridge MCP de Hermes está disponible y listado entre las tools MCP de la sesión

#### Scenario: Otro repo del ecosistema no hereda el bridge
- **WHEN** se abre una sesión de Claude Code en un repo distinto (`contexia-brain`,
  `contexia-ops-template`, etc.)
- **THEN** el bridge MCP de Hermes de `antigravity-app` no aparece registrado ahí

### Requirement: El bridge no expone datos de negocio ni credenciales de producción
El bridge MCP Hermes→Claude Code SHALL limitarse a orquestación de desarrollo (canales, cron,
memoria de Hermes) — nunca a datos de tenant, Shadow GL, ni acciones sobre `approval_queue`.

#### Scenario: Se documenta el alcance del bridge
- **WHEN** se revisa `ARCHITECTURE.md` o `.mcp.json` tras este change
- **THEN** el bridge está explícitamente descrito como herramienta de desarrollo, distinto del
  canal ya existente (4 MCP tools de `contexia_agents/server.py`) que expone datos de negocio en
  sentido inverso (Claude Code → backend de Contexia)
