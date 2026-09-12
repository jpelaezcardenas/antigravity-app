## Context

Este change existe porque la exploración inicial para un bridge MCP Hermes↔Claude Code encontró
dos problemas de base antes de poder construir nada nuevo:

1. **Doc fabricada.** `docs/integrations/HERMES-SELF-CONFIG.md` cita 3 "roles" —
   `centinela-monitor`, `auditoria-runner`, `resolucion-executor` — que no corresponden a ningún
   perfil real (`/home/contexia/.hermes/profiles/`: `default`, `approval-queue`, `auditoria`,
   `centinela`, `contexia`, `kb`, `orchestrator`, `pulso`, `radar`, `social-ops`, `taty`), ningún
   bot real del Electron Desktop (Contexia, Taty, Social Ops, Radar, Kb, Pulso, Approval Queue,
   Centinela, Auditoria, Orchestrator, Hermes), ni ningún job real de los 8 Scheduled Jobs en
   producción. Esto es exactamente el patrón que CLAUDE.md §9 prohíbe (fabricar contenido en vez
   de investigar la fuente real) — aplicado aquí a documentación de infraestructura, no a código.

2. **Bug de producción activo.** El job Social Ops falla con:
   ```
   hermes-refusal-reason: SESSION_NOT_OWNED
   Session 20260829_193718_5b2db1 already has a live owner (cli, pid 44191, lease age 1m).
   ```
   junto con un aviso de que los gateways pueden estar sirviendo "pre-update modules (mixed
   sys.modules)". El job Pulso Diario muestra `error` / "Interrupted by shutdown before terminal
   completion" — probablemente síntoma del mismo problema de gateway, no un bug independiente.

Un tercer dato nuevo, confirmado directamente por el fundador y ausente en `ARCHITECTURE.md` hoy:
existe una **app de escritorio Electron de Hermes en Windows nativo**, distinta del núcleo Hermes
que corre en WSL, que se conecta al backend de Contexia **vía el gateway** (Railway `-175a`,
`/api/v1/*`), nunca directo a Supabase.

**Discrepancia adicional detectada al leer el contexto de OpenSpec (a resolver, no a asumir):** el
contexto del proyecto usado por `openspec instructions` describe `/home/contexia/hermes-workspace/`
(con backup en GitHub `jpelaezcardenas/hermes-workspace` y un `swarm.yaml` de "roles semánticos")
como la fuente de verdad de Hermes. Esto es una ruta y un modelo distintos de
`/home/contexia/.hermes/profiles/` que el fundador mostró en vivo. No se asume cuál es correcta —
se investiga en la Fase 0 de este mismo change (ver Decisiones, más abajo) antes de escribir nada
nuevo en `ARCHITECTURE.md`.

## Goals / Non-Goals

**Goals:**
- Eliminar de la documentación toda referencia a roles/rutas de Hermes que no existen en la
  instalación real.
- Diagnosticar y corregir el bug `SESSION_NOT_OWNED` / gateway desincronizado que hoy causa fallos
  reales en producción (Social Ops, Pulso Diario).
- Dejar `ARCHITECTURE.md` con una descripción de la topología de Hermes (WSL core + Electron
  Desktop + gateway) que el fundador pueda verificar contra lo que ve en pantalla, sin ambigüedad.
- Confirmar de una vez por todas cuál es la fuente de verdad real de la config de Hermes
  (`/home/contexia/.hermes/` vs. `/home/contexia/hermes-workspace/` vs. la ruta Windows
  `AppData\Local\hermes\...` que la Decisión #21 de `ARCHITECTURE.md` ya corrigió una vez) — para
  no repetir el ciclo de "documentar una ruta muerta" una tercera vez.

**Non-Goals:**
- No se construye en este change el bridge MCP Hermes→Claude Code ni ningún loop de auto-fix —
  eso depende de que esta base quede sana, y es un change posterior separado.
- No se toca ningún dato de tenant, Shadow GL, ni ningún endpoint de `/api/v1/*` del backend de
  Contexia — este change es exclusivamente infraestructura local de Hermes + documentación.
- No se automatiza el fix del bug de gateway con un script nuevo — se ejecutan los comandos de
  diagnóstico/reparación (`hermes update`, `hermes gateway restart`, cierre de sesión huérfana)
  manualmente, y se documenta el procedimiento para la próxima vez que ocurra.
- No se migran ni renombran los 11 perfiles existentes — se documentan tal como están.

## Decisions

**D1 — REVERTIDA 2026-09-10, tras verificación directa en la máquina.** La premisa de esta
decisión era incorrecta: `centinela-monitor`/`auditoria-runner`/`resolucion-executor` **no** son
contenido fabricado — existen como definiciones YAML reales y detalladas en
`/home/contexia/.hermes/agents.yaml` (con `system_prompt`, `tools`, `wrapper`, modelo). Lo que sí
se confirmó como falso es que estén conectados al runtime activo de Hermes: `grep -rl
"agents.yaml" hermes_cli/*.py` no arroja resultados, y `swarm` no es un subcomando válido del CLI
(el único "swarm" real en el código fuente es `kanban_swarm.py`, una feature de Kanban sin
relación). **Decisión final aplicada**: no se purgó nada — se corrigió `docs/integrations/
hermes-autoconfig-instruction-2026-08-29.md` (que sí repetía esta info, en un archivo distinto al
que esta decisión asumía) para dejar de afirmar que esos 3 roles están operativos, sin borrar su
existencia real en `agents.yaml`, y redirigiendo a los mecanismos confirmados en producción (10
perfiles reales + 8 Scheduled Jobs + Skills por perfil). Lección: la corrección de una
"fabricación" sospechada debe empezar por verificar el archivo en disco, no por asumir que la
ausencia de un match obvio significa que el contenido no existe en ningún lado.

**D2 — Tratar el bug de gateway como bloqueante de este change, no como ticket aparte.**
Decisión explícita del fundador (capturada en la sesión de planeación): no tiene sentido dejar
pendiente un bug que afecta directamente la confiabilidad de cualquier delegación futura a Claude
Code vía el mismo gateway. Se resuelve aquí, con el criterio de salida objetivo: los 8 Scheduled
Jobs corren su próximo ciclo sin `error` ni `delivery_failed`.

**D3 — No forzar el lease huérfano.**
El propio mensaje de error de Hermes lo advierte explícitamente: "Do not delete a live owner's
lease to force a takeover." Se sigue esa instrucción tal cual — se investiga primero si el proceso
pid 44191 sigue vivo, y solo se cierra la sesión desde su superficie propietaria real (CLI), nunca
borrando el lease a la fuerza desde otro lado.

**D4 — Resolver la discrepancia `.hermes/` vs `hermes-workspace/` antes de escribir doc nueva.**
En vez de asumir cuál ruta es la vigente (ya se cometió ese error una vez con la ruta Windows en
la Decisión #21 de `ARCHITECTURE.md`), este change dedica un paso explícito de Fase 0 a verificar
en la máquina real cuál directorio existe, cuál tiene contenido actualizado, y si ambos coexisten
con roles distintos (ej. uno para el núcleo Hermes, otro para un repo de backup/sync a GitHub).

## Risks / Trade-offs

- **[Riesgo] El bug de gateway puede tener una causa más profunda que un simple restart** (ej. una
  versión de Hermes desactualizada que requiere un update completo, no solo un restart) →
  **Mitigación:** si `hermes gateway restart` no resuelve "mixed sys.modules", escalar a
  `hermes update` completo antes de dar la Fase 0 por cerrada; no declarar éxito solo por ver el
  próximo ciclo correr una vez — observar al menos 2 ciclos completos de Social Ops y Pulso Diario.
- **[Riesgo] Cerrar la sesión con lease huérfano podría interrumpir trabajo real si el proceso pid
  44191 sigue activo** → **Mitigación:** D3 — confirmar el estado del proceso antes de cualquier
  acción; si está vivo, coordinar con el fundador antes de cerrarlo.
- **[Trade-off] Este change no resuelve el bridge MCP que el fundador realmente quiere** → es
  intencional: construir sobre una base con doc fabricada y un gateway fallando habría heredado
  ambos problemas al bridge nuevo. Se acepta el costo de una fase previa para no repetir el patrón
  de "arreglo rápido sobre información no verificada" que CLAUDE.md ya documenta como incidente
  pasado (§9).

## Migration Plan

No hay migración de datos ni despliegue a Railway/Vercel en este change. El "despliegue" es:
1. Editar la documentación en el repo (commit normal a `main`, sin Stage 11 de Vercel/Railway
   porque no hay código de producto tocado).
2. Ejecutar los comandos de reparación de Hermes directamente en la máquina del fundador (WSL +
   Windows), fuera del repo — no hay rollback de código necesario; si `hermes update` causara un
   problema nuevo, el rollback es la propia gestión de versiones de Hermes (fuera del alcance de
   este repo).

## Open Questions

- ¿Cuál es la fuente de verdad real: `/home/contexia/.hermes/profiles/` o
  `/home/contexia/hermes-workspace/` (este segundo con backup a GitHub y `swarm.yaml`)? ¿Coexisten
  con roles distintos? — se resuelve en Fase 0, tasks 0.x.
- ¿Por qué solo el perfil `contexia` tiene "Gateway running" (123 skills) y los otros 10 muestran
  "Gateway stopped" (93 skills c/u, salvo `default` con 98)? ¿Es el diseño esperado (un solo
  gateway activo orquesta a los demás perfiles como sub-agentes) o sí es parte del mismo bug de
  módulos desincronizados?
- El bot "Contexia" en el Electron Desktop — ¿es el agente Orchestrator con otro nombre, o un bot
  general distinto de los 9 agentes documentados? Confirmar antes de declarar el mapeo "1:1
  cerrado" en la doc final.
