<!--
  CANONICAL — How AI agents work on this repo (the operating model / harness).
  Pairs with ARCHITECTURE.md (what the system IS). Identity → .antigravity/GROUND_TRUTH.md wins.
  Pattern reference: github.com/jpelaezcardenas/ejemplo-harness-subagentes (Harness Engineering).
-->

# Contexia — Harness de subagentes (cómo trabajan los agentes)

## Para el fundador (en 1 minuto)

Cuando le pides algo a Claude Code (u otro copiloto) en este repo, **no trabaja de una**:
un **líder** planifica y reparte, un **implementer** hace *una sola cosa* y escribe qué tocó
en un archivo (no en el chat), y un **revisor** valida contra reglas objetivas antes de dar
nada por bueno. Todo queda en `progress/` (en disco, versionado), no en la memoria del chat.
Esto es lo que evita que el repo se vuelva a llenar de archivos sueltos y contradictorios.

Es el patrón del repo de referencia [`ejemplo-harness-subagentes`](https://github.com/jpelaezcardenas/ejemplo-harness-subagentes),
adaptado a Contexia y montado **encima** de OpenSpec (no lo reemplaza).

## El bucle

```
planificar  →  delegar  →  verificar  →  consolidar memoria
 (líder lee     (subagentes   (reviewer +   (progress/history.md
  canon +        escriben a     init.sh       + MEMORY.md; chat
  change activo) progress/)     verde)        es desechable)
```

## ¿Choca con OpenSpec? No — lo envuelve (4 capas + precedencia)

Harness = **cómo** trabajan los agentes. OpenSpec = **qué/con qué contrato**. Precedencia (arriba manda):

| Capa | Rol | Artefacto | Precedencia |
|---|---|---|---|
| 1. Canon vivo | Identidad + arquitectura + agentes | `GROUND_TRUTH.md`, `ARCHITECTURE.md`, `HARNESS.md`, `AGENTES.md` | Gana en identidad/arquitectura |
| 2. Estándares | Dominio, stack, patrones | `openspec/config.yaml`, `docs/*-standards.md`, `CLAUDE.md` | Gana en "cómo construir" |
| 3. Delta de cambio | Qué se modifica AHORA | `openspec/changes/<id>/tasks.md` | **Única fuente del "qué ahora"** |
| 4. Ejecución | plan → subagentes → verificación → memoria | `.claude/agents/`, `progress/`, `feature_list.json`, `init.sh` | Ejecuta la capa 3, no la redefine |

**Regla de oro:** la capa 4 NUNCA inventa alcance. `feature_list.json` es un **puntero fino**
al change OpenSpec activo (hace cumplir "una cosa a la vez"), no un tracker rival. La lista de
tareas autoritativa siempre es `openspec/changes/<id>/tasks.md`.

## Mapa: repo de referencia ↔ Contexia (por qué no duplica)

| Pieza del repo ejemplo | Equivalente en Contexia | Nota |
|---|---|---|
| `AGENTS.md` (divulgación progresiva) | `CLAUDE.md` + `ARCHITECTURE.md` | Canon vivo, auto-cargado |
| `.claude/agents/` leader/implementer/reviewer | `.claude/agents/` (nuevos) + skill `adversarial-review` = reviewer | El hueco que se cerró |
| `feature_list.json` (una a la vez) | `feature_list.json` (puntero) + `openspec/changes/` | OpenSpec = alcance real |
| `CHECKPOINTS.md` | `DEPLOYMENT_STAGE/CHECKPOINTS.md` | Ya existía — se reutiliza |
| `init.sh` (gate verde) | `init.sh` (estructura + invariante + tests opt-in) | Adaptado a repo grande |
| `progress/` (estado en disco) | `progress/` (nuevo) | Reemplaza el volcado a la raíz |
| memoria durable | `MEMORY.md` + `progress/history.md` | Ya existía |

## Los subagentes

- **`.claude/agents/leader.md`** — planifica, lee canon + change activo, delega, consolida. NO edita código.
- **`.claude/agents/implementer.md`** — implementa UNA tarea de `tasks.md` (TDD), escribe `progress/impl_<id>.md`. NO se autoaprueba.
- **`.claude/agents/reviewer.md`** — valida contra `ARCHITECTURE.md` + estándares + `CHECKPOINTS.md`, escribe `progress/review_<id>.md`. NO edita.
- **Anti teléfono-descompuesto**: los subagentes escriben a `progress/` y devuelven solo una referencia (`done -> progress/impl_<id>.md`). El código no circula por chat.

## Gobernanza multi-herramienta (agencia AAA)

Varios copilotos, **distinta responsabilidad, mismo canon**:

- **Claude Code** — coordinador principal sobre el repo + ejecutor de subagentes (`.claude/agents/`).
- **Codex** — motor de paralelización: exploración/implementación por lotes + verificación paralela, consolida una respuesta.
- **Antigravity** — entorno de producto donde se materializa el MVP, alineado al canon.
- **Hermes** — harness **local** + memoria aplicada (soberanía de datos). Rol único; **NO** autoridad duplicada.

Condición de éxito: eliminar duplicidades de canon y respetar la precedencia de arriba. Si dos documentos gobiernan la misma decisión, gana el de capa más alta y el otro apunta a él.

## Verificación (init.sh)

`./init.sh` es el gate verde: valida que el canon y la estructura del harness existen y la
invariante "un change a la vez". Corre al **empezar** una sesión y **antes** de dar una tarea
por `done`. Tests completos del backend: `RUN_TESTS=1 bash init.sh` (o el reviewer/CI por change).

## Activar los hooks (opcional)

Por seguridad, los hooks NO se auto-instalan (ensanchan permisos). Para activarlos, fusiona
los bloques `hooks` y `permissions` de [`harness-hooks.example.json`](harness-hooks.example.json)
dentro de `.claude/settings.json` (o `.claude/settings.local.json`) tú mismo. El hook `Stop`
corre `init.sh` de forma **no bloqueante** (solo informa) al cerrar sesión.

## Anexo — patrón de referencia

- Repo: [`jpelaezcardenas/ejemplo-harness-subagentes`](https://github.com/jpelaezcardenas/ejemplo-harness-subagentes) (Harness Engineering: el repo ES el sistema, orquestación líder-trabajador-revisor, supervisión por checkpoints).
- Adaptaciones para Contexia: (1) inglés en artefactos técnicos (estándar del repo); (2) `feature_list.json` como puntero a OpenSpec en vez de tracker de alcance; (3) `init.sh` que hard-gatea estructura/canon (tests pesados opt-in); (4) hooks opt-in por seguridad; (5) reutiliza `DEPLOYMENT_STAGE/CHECKPOINTS.md` y el skill `adversarial-review`.
