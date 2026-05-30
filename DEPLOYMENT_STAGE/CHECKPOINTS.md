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

---

## Preguntas para Auto-Revisar

Antes de marcar un checkpoint ✅, pregúntate:

- ¿Alguien más puede verificar esto sin mi explicación?
- ¿Es binario (sí/no) o tiene grises?
- ¿Si alguien más lo hace mañana, entiende exactamente qué hacer?

Si respondiste "no" a alguna, el checkpoint no está listo.
