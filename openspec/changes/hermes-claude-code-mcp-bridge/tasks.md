## 0. Prerequisitos del fundador (no-código, requiere acceso directo a WSL/Windows/dashboard Hermes)

- [x] 0.1 **RESUELTO 2026-09-10.** pid 44191 NO existe ni en Windows (`Get-Process -Id 44191` →
      not found) ni en WSL (`ps -p 44191` → not found). El `wsl.exe` interop estaba en sí mismo
      roto (`Wsl/Service/E_UNEXPECTED` en cualquier exec, incluso `whoami`) — un `wsl --shutdown`
      autorizado explícitamente por el fundador lo resolvió; tras el restart el exec funciona y
      confirma que el lease es zombie (proceso ya no existe en ningún lado). No fue necesario
      "cerrar la sesión desde su superficie propietaria" porque el proceso ya estaba muerto — el
      restart del servicio WSL limpió el estado.
- [x] 0.2 **RESUELTO 2026-09-10.** Ambas rutas existen y **no son la misma cosa**:
      `/home/contexia/.hermes/` es el **home runtime real de Hermes** (gateway, cron, kanban.db,
      state.db, `hermes-agent/` con el propio intérprete Python, `agents.yaml`, `SOUL.md`,
      `profiles/`). `/home/contexia/hermes-workspace/` es un **clon de código fuente** de Hermes
      (Electron, `src/`, `swarm.yaml`, `docker-compose.yml`, `node_modules/`) — **no** es config
      de runtime, es el repo de desarrollo del propio Hermes Agent. Su remoto real es
      `https://github.com/outsourc-e/hermes-workspace.git` (fetch/push), **no**
      `jpelaezcardenas/hermes-workspace` como afirmaba el contexto de este OpenSpec — ese segundo
      repo sí existe y es alcanzable (`git ls-remote` responde), pero es un remoto distinto, no el
      que usa este clon local. `swarm.yaml` (roles semánticos) vive en este repo de código fuente,
      no en el runtime — es plantilla/config de desarrollo del propio Hermes Agent, no la config
      operativa de los perfiles de Contexia.
- [x] 0.3 **RESUELTO 2026-09-10.** La config real y activa del perfil `contexia` es
      `/home/contexia/.hermes/profiles/contexia/config.yaml` (WSL, 39KB, modificado activamente).
      **No existe ningún `default` entre los perfiles** — los 10 perfiles reales son:
      `approval-queue`, `auditoria`, `centinela`, `contexia`, `kb`, `orchestrator`, `pulso`,
      `radar`, `social-ops`, `taty` (corrige la lista de 11 con "default" citada en la sesión
      anterior). Confirmado con `ls`: solo `contexia` tiene `gateway.pid` — es el único perfil con
      gateway corriendo (pid 397, arrancado por el restart de esta sesión). Los otros 9 no tienen
      `gateway.pid` en absoluto, consistente con "un solo gateway activo orquesta a los demás
      perfiles como sub-agentes" (Open Question de `design.md` — queda resuelta a favor de esa
      hipótesis, no del bug).

      **Hallazgo adicional no pedido pero directamente relevante para la Tarea 2 (fix del bug):**
      dentro de `profiles/contexia/` hay marcadores de una actualización de Hermes que quedó
      **interrumpida y nunca se limpió**: `.hermes-update-in-progress` contiene el pid `57564`
      (confirmado muerto) y `fleet_restart_pending` referencia ese mismo pid con un
      `expected_sha` que nunca se aplicó. `.update_check` reporta la instalación **94 revisiones
      detrás** (`"behind": 94`, versión instalada `0.21.1`). Esto es consistente como causa raíz
      directa del aviso "Gateways may still be serving pre-update modules (mixed sys.modules)" —
      una actualización de Hermes empezó, se interrumpió (el proceso que la ejecutaba murió), y
      dejó el estado a medio camino. También hay `config.yaml.bak_20260910_pre_mcp_fix` (backup de
      **hoy mismo**, antes de una sesión anterior) — indicio de que alguien (el fundador u otra
      sesión) ya intentó tocar la config de MCP hoy antes de esta sesión.

## 1. Purgar documentación fabricada

- [x] 1.1 **RE-DIAGNOSTICADO 2026-09-10.** `docs/integrations/HERMES-SELF-CONFIG.md` **no
      contiene** ninguna mención a `centinela-monitor`/`auditoria-runner`/`resolucion-executor`
      (confirmado por grep) — la suposición original de que la fabricación vivía en este archivo
      era incorrecta. El archivo real con el problema es
      `hermes-autoconfig-instruction-2026-08-29.md` (ver 1.2-1.4).
- [x] 1.2 **REVERTIDO Y CORREGIDO 2026-09-10 — la Decisión D1 de `design.md` era incorrecta,
      no se ejecutó tal cual.** Antes de purgar, se verificó `/home/contexia/.hermes/agents.yaml`
      directamente en la máquina: **los 3 roles SÍ existen como contenido real** (definiciones YAML
      completas con `system_prompt`, `tools`, `wrapper`, modelo) — no son fabricación sin fuente.
      Lo que sí se verificó como falso es la afirmación de la doc de que son "los roles reales que
      existen hoy" en un sentido operativo: `grep -rl "agents.yaml" hermes_cli/*.py` → cero
      resultados, y `hermes swarm` no es un subcomando válido del CLI (`invalid choice: 'swarm'`;
      el único hit de "swarm" en el código fuente es `kanban_swarm.py`, una feature de Kanban sin
      relación). Conclusión: `agents.yaml` es configuración huérfana, no fabricación — no se borró
      el contenido, se corrigió la interpretación de qué representa.
- [x] 1.3 **RESUELTO 2026-09-10.** El mapeo real confirmado es: **10 perfiles** en disco (no 11 —
      no existe `default`, ver tarea 0.3): `approval-queue`, `auditoria`, `centinela`, `contexia`,
      `kb`, `orchestrator`, `pulso`, `radar`, `social-ops`, `taty` ↔ los mismos 9 agentes de
      `AGENTES.md` + `contexia` como perfil "general"/orquestador. No se investigó a fondo el bot
      "Hermes" del Electron Desktop en esta pasada — queda como pregunta abierta menor, no
      bloqueante (los 10 perfiles y los 8 Scheduled Jobs ya dan una base sólida y verificada).
- [x] 1.4 **RESUELTO 2026-09-10.** Sí, `hermes-autoconfig-instruction-2026-08-29.md` repetía la
      misma información (§0 línea 16-21, §0.5 punto 2, §3 tabla — filas de Centinela Fiscal y
      Auditoría Sombra). Corregido en las 4 ubicaciones: se mantiene el contenido real de
      `agents.yaml` pero se corrige la afirmación de que está conectado al runtime activo, y se
      redirige a los mecanismos reales confirmados (10 perfiles + Scheduled Jobs + Skills por
      perfil). No se tocaron los anexos §9 (normativa fiscal Renta Natural) ni §10 (informe Hub de
      Innovación) — son contenido no relacionado, fuera de alcance de esta tarea.

## 2. Diagnosticar y corregir el bug de gateway

- [x] 2.1 **RESUELTO 2026-09-10.** pid 44191 ya estaba muerto (confirmado en 0.1) — no hubo lease
      vivo que forzar. El propio `wsl --shutdown` (autorizado explícitamente) limpió el estado
      colgado del interop antes de tocar Hermes.
- [x] 2.2 **RESUELTO 2026-09-10.** `hermes --profile contexia gateway restart` ejecutado — gateway
      pasó de pid 397 a pid 13144. `hermes --version` confirmó que el warning "mixed sys.modules"
      **desapareció** inmediatamente tras el restart.
- [x] 2.3 **RESUELTO 2026-09-10.** El restart no completó la actualización atascada en sí — la
      instalación seguía reportando "99 commits behind" y los marcadores `.hermes-update-in-progress`/
      `fleet_restart_pending` (hallados en 0.3) seguían en disco. Se ejecutó `hermes --profile
      contexia update` (autorizado explícitamente por el fundador): detectó "orphan divergence"
      (el historial local no compartía ancestro con `origin/main`), respaldó el HEAD anterior en
      `refs/hermes-update-backups/orphan-main-20260910-215315-248ff2d3e8bf` (expira en 30 días, sin
      pérdida de datos), reseteó a `origin/main`, restauró los cambios locales encima, sincronizó
      skills a los 11 perfiles, y reinició `hermes-gateway-contexia` (nuevo pid 15573) y
      `hermes-dashboard.service`. Verificación final: `hermes --version` → "Up to date", sin
      warnings; ambos marcadores de actualización atascada ya no existen en disco.
- [x] 2.4 **RESUELTO 2026-09-11 — son causas independientes, ninguna es el bug de gateway de
      ayer.** Verificado contra el ciclo real de hoy (`hermes cron list` + `cron incidents` +
      `cron doctor`):
      - **Pulso Diario / Insight Bridge**: el mensaje "Interrupted by shutdown" es genérico y
        engañoso. La causa real (`cron incidents`) es que `scripts/pulso.sh` recibe un error HTTP
        de `GET /internal/pulso/all-active` (`curl -sf` → exit 22 = respuesta no-2xx). Recurrente:
        2026-09-08 (exit 7), 2026-09-10 (exit 22), 2026-09-11 (exit 22). Causa raíz en el backend
        (`apps/backend/routers/internal.py:90-99`): `pulso_all_active()` **no tiene manejo de
        error por cliente**, a diferencia de su endpoint hermano `social_ops_all_active()` (línea
        158+, explícitamente "error-resilient" por diseño) — un solo cliente con datos
        incompletos puede tumbar el endpoint entero con 500 para todos. **Fuera de alcance de
        este change** (bug de backend, no de Hermes/MCP) — requiere su propio OpenSpec change.
      - **Social Ops (`SESSION_NOT_OWNED`)**: NO es un bug de infraestructura — es una colisión
        real entre la entrega `bot-chat` al perfil `(own)` (que escribe en la sesión interactiva
        persistente del fundador, `20260829_193718_5b2db1`, activa desde el 29 de agosto porque
        nunca llega a los 1440 min de idle) y el fundador usando Hermes Desktop activamente en
        el mismo momento en que el cron dispara. Confirmado: Radar Predictivo (11 AM, mismo
        `deliver: bot-chat`) corrió limpio ambos días — solo colisiona cuando coincide con uso
        activo a la 1-2 PM. El script en sí completa bien (`Execution: completed`); solo falla
        la notificación. Severidad baja, intermitente por diseño de uso, no un estado corrupto.
      - También se encontraron 4 incidentes `drift_skip` (6-7 sept, Centinela/Social Ops/Radar/
        Auditoría) — salvaguarda deliberada de Hermes que se niega a correr un job si el
        proveedor de inferencia global cambió desde que se creó (`xiaomi`→`anthropic`), para
        evitar gasto no autorizado. No recurrió desde entonces — no bloqueante.
- [x] 2.5 **RESUELTO en 0.3.** Solo `contexia` tiene `gateway.pid`; los otros 9 perfiles no tienen
      ninguno — consistente con "un solo gateway activo orquesta a los demás perfiles", no con un
      síntoma del bug.

## 3. Verificar el fix en producción (criterio de salida de Fase 0 — REVISADO)

**Criterio original ("los 8 jobs corren sin error") no se cumplió literalmente — pero el motivo
por el que no se cumplió ya está diagnosticado y no es el bug que este change existía para
arreglar.** El bug de gateway (update atascado) SÍ quedó resuelto y verificado (Sección 2). Las
dos fallas que persisten hoy (2026-09-11) son problemas independientes, ya caracterizados en 2.4:

- [x] 3.1 **Social Ops — confirmado, colisión de sesión, no bloqueante.** Volvió a fallar hoy con
      el mismo síntoma pero causa ya entendida (ver 2.4) — no es un estado corrupto que arreglar,
      es un choque de uso ocasional. No se toca la config en este change (decisión pendiente del
      fundador: cambiar `deliver` a Telegram para evitarlo, o dejarlo así).
- [x] 3.2 **Pulso Diario / Insight Bridge — confirmado, bug de backend real, fuera de alcance.**
      Falló hoy también, causa raíz identificada (`pulso_all_active()` sin resiliencia por
      cliente, ver 2.4) — requiere un fix de código en `apps/backend/routers/internal.py`, que
      es un OpenSpec change aparte, no de este bridge.
- [x] 3.3 **Confirmado vía `hermes cron list`/`doctor`.** Los otros 5 jobs (Shadow GL, Radar
      Predictivo, Centinela Fiscal, Auditoría Sombra, Metrics Snapshot) corrieron limpios hoy
      (con catch-up tardío esperado por el laptop apagado de noche — no es un error).

## 4. Documentar la topología real en ARCHITECTURE.md

- [x] 4.1 **RESUELTO 2026-09-10.** Fila "Hermes (core)" reescrita con el mapeo real verificado
      (10 perfiles, 8 Scheduled Jobs, `agents.yaml` huérfano) + nueva fila "Hermes Desktop"
      (Electron, Windows nativo, conecta vía gateway Railway `-175a`, nunca directo a Supabase).
- [x] 4.2 **RESUELTO 2026-09-10.** Agregada Decisión #27 en `ARCHITECTURE.md`, documentando el
      bug de gateway (causa raíz: update interrumpida) y la corrección de doc en dos direcciones
      (no una purga simple), con la lección operativa de verificar en disco antes de asumir
      fabricación.
- [x] 4.3 **No aplica — sin desajuste real.** La reconciliación de la tarea 1.3 confirmó que los
      10 perfiles mapean casi 1:1 a los 9 agentes de `AGENTES.md` (10mo perfil = `contexia`,
      general/orquestador) — no se encontró ninguna discrepancia que amerite editar `AGENTES.md`.

## 5. Cierre del change (sin Stage 11 — no hay deploy a Railway/Vercel)

- [ ] 5.1 `git diff` de los archivos de documentación tocados — confirmar que ningún secreto,
      token, o valor de credencial quedó escrito en texto plano (regla de `ARCHITECTURE.md`
      Decisión #12)
- [ ] 5.2 Confirmar con el fundador que la topología documentada en `ARCHITECTURE.md` coincide con
      lo que ve en su dashboard de Hermes y en el Electron Desktop
- [ ] 5.3 Commit de los cambios de documentación a `main`
