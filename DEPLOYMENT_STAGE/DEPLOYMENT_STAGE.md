# OpenSpec Deployment Stage — Cierre del Loop a Producción

**Propósito:** Garantizar que OpenSpec no solo completa tareas documentadas, sino que **cierra el ciclo hasta cambios LIVE en producción**.

---

## Principio Central

```
OpenSpec tradicional:
  proposal → design → spec → tasks → apply → archive ✅
  
OpenSpec + Deployment:
  proposal → design → spec → tasks → apply → [DEPLOY] → archive ✅
                                              ↑ NUEVO
```

**Sin Deployment Stage:** tarea "terminada" ≠ cambios en vivo.  
**Con Deployment Stage:** "terminada" = verificado LIVE en producción.

---

## Stage 11: Deploy to Production (MANDATORY)

### 11.1 Commit & Push

```bash
# Desde la raíz del repo
git add -A
git commit -m "feat(CHANGE-ID): [descripción corta]

Closes OpenSpec change: [CHANGE-ID]
OpenSpec tasks: all complete, ready for deployment."
git push origin [deploy-branch]
```

**Validación:**
- [ ] Commit aparece en `git log --oneline -1`
- [ ] Push exitoso (sin errores de auth)
- [ ] Rama remota está 1 commit adelante

---

### 11.2 Verificar Pipeline de Deploy

#### Si tu proyecto usa **Vercel** (frontend):
```bash
# Verifica que el build fue disparado:
# 1. Abre https://vercel.com/[tu-proyecto]/deployments
# 2. Busca el commit hash: git rev-parse --short HEAD
# 3. Espera que aparezca build "Processing" → "Ready"
```

Checklist:
- [ ] Vercel detectó el push
- [ ] Build status: ✅ READY (verde)
- [ ] Tiempo de build: < 3 min (normal)
- [ ] No hay errores en Vercel logs

#### Si tu proyecto usa **Railway** (backend):
```bash
# Verifica que el deploy fue disparado:
# 1. Abre https://railway.app/[tu-proyecto]/deployments
# 2. Busca el deployment más reciente
# 3. Status debe estar: "Success" o "Active"
```

Checklist:
- [ ] Railway detectó el push
- [ ] Deploy status: ✅ SUCCESS o ✅ ACTIVE
- [ ] Tiempo de deploy: < 5 min (normal)
- [ ] No hay errores en Railway logs

---

### 11.3 Verificar Cambios en Vivo

```bash
# Hard refresh en navegador
# Windows/Linux: Ctrl+F5
# Mac: Cmd+Shift+R

# O via curl (si es una API):
curl -s https://[production-url]/[endpoint] | jq .
```

Checklist:
- [ ] Abres la URL de producción
- [ ] Hard refresh (no cache)
- [ ] Cambios esperados son visibles
- [ ] No hay errores en console del navegador (F12)
- [ ] No hay errores 500/502/503

---

### 11.4 Plan de Rollback (por si falla)

**Si los cambios rompieron algo:**

```bash
# 1. Identifica el último commit bueno
git log --oneline -5
# Busca el hash anterior a tu commit

# 2. Revert (crea un commit que deshace el cambio)
git revert [hash-de-tu-commit]
git push origin [deploy-branch]

# 3. Verifica que el rollback fue a producción
# (repite paso 11.2 y 11.3)

# 4. Abre issue/bug para investigar qué falló
```

Checklist:
- [ ] Sabes cuál fue el último commit bueno
- [ ] Pusheaste git revert
- [ ] Vercel/Railway volvió a desplegar
- [ ] Producción está de nuevo estable

---

### 11.5 Cierra el Loop

**Crea reporte de deployment:**

```bash
mkdir -p openspec/changes/[CHANGE-ID]/reports
```

**Contenido:** `openspec/changes/[CHANGE-ID]/reports/YYYY-MM-DD-deployment.md`

```markdown
# Deployment Report — [CHANGE-ID]

## Resumen
- Fecha: [YYYY-MM-DD]
- Commit: [git rev-parse --short HEAD]
- Branch: [deploy-branch]
- Status: ✅ LIVE

## Timeline
- 11.1 Push: [HH:MM UTC]
- 11.2 Build complete: [HH:MM UTC] (Vercel/Railway)
- 11.3 Verificado en vivo: [HH:MM UTC]

## URLs Verificadas
- [ ] https://[production-url/section1]
- [ ] https://[production-url/section2]
- [ ] https://[api-endpoint] (if applicable)

## Screenshots
- before-deployment.png: [describe]
- after-deployment.png: [describe]

## Rollback
- Last good commit: [hash]
- Rollback command: git revert [hash]
```

**Sube el reporte a git:**
```bash
git add openspec/changes/[CHANGE-ID]/reports/YYYY-MM-DD-deployment.md
git commit -m "docs: deployment report for [CHANGE-ID]"
git push
```

Checklist:
- [ ] Reporte creado con screenshots
- [ ] Reporte commiteado y pusheado
- [ ] Visible en `git log --oneline`
- [ ] Marcas Stage 11 como ✅ DONE

---

## Qué Significa "Terminado"

Una OpenSpec change está **verdaderamente terminada** cuando:

```
✅ Spec propuesta y documentada
✅ Tareas completadas (tasks.md marcadas)
✅ Código implementado y testeado
✅ PR revisado y mergeado
✅ [NUEVO] Cambios verificados LIVE en producción
✅ Deployment report creado
✅ Change archivado
```

Sin el paso 11 (deployment), el change **no está verdaderamente terminado**.

---

## Excepciones

**No aplica Stage 11 si:**
- Es una change puramente documental (README, specs, no código)
- Es una change de "backend-only" que no tiene URL visible (comunica antes de aplicar)

**En esos casos:**
- Marca Stage 11 como "N/A — [razón]"
- El reviewer debe validar que la razón es válida

---

## Self-Improving Loop

Cada vez que Stage 11 falla:
1. El implementer documenta la razón
2. El reviewer propone qué añadir a `CHECKPOINTS.md`
3. Se añade a CHECKPOINTS.md la nueva regla
4. Próximos changes incluyen esa regla desde el inicio

Ejemplo:
```
Sesión 1: Stage 11 falla porque olvidaron git push
Sesión 2: CHECKPOINTS.md ahora dice "Verify git push succeeded"
Sesión 3+: Todos hacen git push sin olvidar
```

---

## References

- `CHECKPOINTS.md` — criterios objetivos de "tarea terminada"
- `checklist-vercel.md` — pasos específicos para Vercel
- `checklist-railway.md` — pasos específicos para Railway
- `INTEGRATION_GUIDE.md` — cómo integrar Stage 11 a cada proyecto
