# CHECKPOINTS — Criterios Objetivos de "Tarea Terminada"

**Propósito:** Definir explícitamente qué significa "hecho" en cada stage de OpenSpec.

Cada checkpoint es una regla binaria (✅ sí / ❌ no). Sin grises.

---

## Stage 0: Setup

- [ ] Feature branch creada: `feature/[CHANGE-ID]`
- [ ] Rama local tracking remoto
- [ ] `git status` limpio (sin cambios uncommitted de trabajo anterior)

---

## Stage 1: Propuesta

- [ ] `proposal.md` existe y es legible
- [ ] "Summary" ≤ 3 párrafos
- [ ] "Why" explica el problema, no la solución
- [ ] "Scope" lista items concretos, no vagos
- [ ] "Success Signals" son verificables (no "mejor", "más rápido")

---

## Stage 2: Diseño

- [ ] `design.md` existe
- [ ] Diagrama o pseudocódigo para flujos nuevos
- [ ] Dependencias documentadas (otras features, librerías)
- [ ] Trade-offs explicados si hay múltiples opciones
- [ ] No hay referencias a "TBD" sin fecha/dueño

---

## Stage 3: Spec

- [ ] `specs/[CHANGE-ID]/spec.md` existe
- [ ] Endpoints / métodos listados con entrada/salida
- [ ] Database schema (si aplica) documentado
- [ ] Error cases documentados (qué pasa si fallan)
- [ ] Migrations / DDL (si aplica) incluidas

---

## Stage 4: Tasks

- [ ] `tasks.md` existe con todas las secciones
- [ ] Cada tarea es ≤ 30 min de trabajo
- [ ] Tasks tienen dueño asignado o explícitamente "auto"
- [ ] No hay tareas bloqueadas sin decir por qué
- [ ] Stage 11 (Deploy) está listado como tarea final

---

## Stage 5: Implementación (Apply)

### Código
- [ ] Código compilable / sin syntax errors
- [ ] Tests existentes pasan
- [ ] Tests nuevos pasan
- [ ] Linting pasa (prettier, eslint, ruff, etc.)
- [ ] Type checking pasa (TypeScript, mypy, etc.)

### Documentación
- [ ] README actualizado si hay cambios de instalación
- [ ] Comentarios en código para lógica no-trivial
- [ ] Ningún TODO sin asignar o fecha
- [ ] **Docs-sync (canon vivo):** si el cambio agregó/quitó/modificó un contenedor o dependencia externa → `ARCHITECTURE.md` actualizado en ESTE cambio; si hubo una decisión arquitectónica significativa → nueva línea en "Decisiones asentadas" de `ARCHITECTURE.md` (ver `HARNESS.md`)

### Database
- [ ] Migrations están en `migrations/` o equivalente
- [ ] Schema matches spec.md
- [ ] Rollback strategy documentada

---

## Stage 6: Review

- [ ] Code review completada (changelog, PR comments resolved)
- [ ] Tests coverage ≥ 80% (si aplica)
- [ ] No hay "FIXME" or "HACK" comentarios sin issue abierto
- [ ] Performance acceptable (no N+1 queries, etc.)
- [ ] Security review passed (no hardcoded secrets, input validation, etc.)

---

## Stage 7: Deploy

### Pre-Deploy
- [ ] Todos los cambios están en rama remota
- [ ] CI/CD pipeline verde (todas las checks pasan)
- [ ] Feature branch está up-to-date con `main`

### Deployment
- [ ] Commit pusheado con mensaje descriptivo
- [ ] Vercel/Railway build completado exitosamente
- [ ] No hay errores en deploy logs

### Post-Deploy
- [ ] Cambios verificados en URL de producción
- [ ] Hard refresh muestra cambios esperados
- [ ] Console del navegador: sin errores
- [ ] API endpoints responden (si aplica)

### Documentación
- [ ] Deployment report creado en `reports/YYYY-MM-DD-deployment.md`
- [ ] Report incluye: commit hash, Vercel/Railway build URL, screenshots before/after
- [ ] Report pusheado a rama

---

## Stage 8: Cierre

- [ ] Todos los checkpoints anteriores están ✅
- [ ] No hay PRs abiertos o en "review" estado
- [ ] Reporte de deployment visible en git
- [ ] Change está listo para `/opsx:archive`

---

## Excepciones Documentadas

Si un checkpoint no aplica, marca como **N/A + razón**:

```
- [N/A] Tests coverage ≥ 80% — Razón: cambio solo docs, no código
```

**Pero:** N/A requiere revisión explícita por el reviewer.

---

## Self-Improving Rule

Cuando un reviewer rechaza una tarea por una razón **nueva** (no en este documento):

1. Documenta la razón aquí
2. Añade un checkpoint nuevo
3. Próximas tareas usan este checkpoint desde Stage 4

**Ejemplo de evolución:**
```
Sesión 1: Reviewer rechaza porque falta env var en .env.example
Sesión 2: CHECKPOINTS agrega "[ ] .env.example tiene todas las vars nuevas"
Sesión 3+: Todos incluyen .env.example en sus tasks
```

**Regla añadida (2026-07-23, `hermes-task-queue-tenant-scoping`):** `RUN_TESTS=1 bash init.sh`
corre el backend suite SIN filtrar, y reportará `[FAIL]` para cualquier cambio mientras existan
~40 fallas pre-existentes no relacionadas (Shadow GL CSV, approval-rules docs/migration checks,
wizard, centinela, secure-LLM, model-selector) y un bug de subprocesos pytest anidados sin
terminar en `tests/test_shadow_gl_stage8_e2e.py` (ver task_id spawneado para su fix). Hasta que
esas fallas se resuelvan o `init.sh` evolucione a comparar contra un baseline en vez de exigir
exit-code 0 absoluto:
- [ ] Nuevo checkpoint: el reviewer DEBE correr los tests del cambio en aislamiento
      (`pytest tests/test_<módulos-tocados>.py -v`) Y el suite completo, y confirmar por nombre
      que cualquier falla del suite completo ya existía antes de esta rama (no solo confiar en el
      exit code de `init.sh`) antes de marcar Stage 6/10 como verde.

**Regla añadida (2026-09-17, migración PWA V2):** un solo día produjo 4 incidentes en
producción por saltarse el mismo tipo de verificación — deploy manual (`Copy-Item`
+ `git add`/`commit`/`push`) sin gate, sin checklist, sin verificación live antes de
seguir al siguiente cambio. `contexia-app/` (fuente) → `out/` (build) → raíz del repo
(artefacto sincronizado a mano, nunca vía CI) es un patrón previamente frágil: los
mismos dos bugs de sync ya habían ocurrido antes (`f6ac8bc`, `5febc01`) y volvieron a
pasar 3 veces más el mismo día porque nada los atrapaba automáticamente.

- [ ] **Rutas nuevas**: toda ruta nueva en `contexia-app/app/**` que use un segmento con
      guion o cualquier nombre fuera del patrón ya cubierto necesita su propio rewrite
      explícito en `vercel.json` (`"/app/<ruta>" → "/app/<ruta>.html"`) ANTES del deploy —
      el catch-all `/app/:path*` cae a `/404.html`. Verificar con
      `grep '"/app/<ruta>"' vercel.json` antes de commitear.
- [ ] **Sync completo**: después de `npm run build`, `git status --short _next/` debe
      mostrarse y sus archivos nuevos deben quedar en el commit — no solo `app/`. Cada
      build de Next genera nombres de chunk con hash nuevo; "ya estaba ahí" nunca aplica.
      Usar `scripts/deploy-pwa.ps1` (nuevo, ver más abajo) en vez de copiar a mano.
- [ ] **CACHE_VERSION**: si el build cambió cualquier HTML o `_next/static/*` servido
      (prácticamente cualquier build con cambios reales), `sw.js` (raíz, el artefacto
      real que sirve Vercel — no solo `contexia-app/public/sw.js`) DEBE traer un
      `CACHE_VERSION` distinto al del commit anterior. `scripts/deploy-pwa.ps1` lo hace
      automático; si se sincroniza a mano, verificar con
      `git diff HEAD~1 -- sw.js | grep CACHE_VERSION`.
- [ ] **Verificación post-deploy con reintento**: un deploy `READY` en Vercel no implica
      que todas las regiones del edge ya sirvan el contenido nuevo — se observó una ruta
      con 404/CSS-404 durante ~90s después de `READY`. Correr
      `pwsh scripts/verify-deploy.ps1 -Routes <rutas-tocadas>` (reintenta con backoff)
      antes de declarar el deploy verificado, no un solo `curl` inmediato tras el push.
- [ ] **Un incidente, un commit de fix, una verificación — antes de seguir.** No encadenar
      3+ pushes seguidos sobre el mismo problema sin confirmar cada uno en vivo; cada push
      sin verificar fue exactamente el patrón que produjo el siguiente incidente.

Scripts nuevos (`scripts/deploy-pwa.ps1`, `scripts/verify-deploy.ps1`) cierran (2) y (4)
automáticamente; (1) y (3) siguen siendo criterio humano antes de commitear.

---

## Preguntas para Auto-Revisar

Antes de marcar un checkpoint ✅, pregúntate:

- ¿Alguien más puede verificar esto sin mi explicación?
- ¿Es binario (sí/no) o tiene grises?
- ¿Si alguien más lo hace mañana, entiende exactamente qué hacer?

Si respondiste "no" a alguna, el checkpoint no está listo.
