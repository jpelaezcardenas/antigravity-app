# Checklist Vercel — Deploy Frontend a Producción

**Aplica a:** Proyectos que usan Vercel para frontend (antigravity-app, contexia.online, etc.)

---

## Pre-Deploy (en tu laptop)

- [ ] Todos los cambios están en `git status --short` del repo local
- [ ] Hiciste `git add`, `git commit -m "[message]"` (no `git commit -am`, siempre explícito)
- [ ] `git log --oneline -1` muestra tu commit
- [ ] `npm run build` pasa sin errores (local test)
- [ ] `npm run test` pasa sin errores (si existen tests)

---

## Push a Remoto

```bash
# Verifica tu rama local
git branch --show-current
# Debería ser: main, develop, o feature/[CHANGE-ID]

# Push
git push origin [current-branch]

# Verifica que el push fue exitoso
git push -v --dry-run  # Opcional: simula sin hacer nada
# O simplemente: git log --oneline -5 && git status
```

Checklist:
- [ ] `git push` terminó sin errores de auth
- [ ] No ves "Permission denied" ni "rejected"
- [ ] Rama remota se actualizó (puedes verificar en GitHub)

---

## Vercel: Espera el Build

**URL:** https://vercel.com/contexia/[project-name]/deployments

1. Abre esa URL
2. Busca tu commit (usa `git rev-parse --short HEAD` para el hash)
3. Espera a que aparezca en la lista de deployments

Estados posibles:
```
Processing → Building → Ready ✅     (éxito)
Processing → Building → Error ❌     (falla)
```

Checklist:
- [ ] Tu commit aparece en Vercel deployments (dentro de 30 seg)
- [ ] Status es "Building" o ya "Ready"
- [ ] Hace NO más de 3 minutos desde el push
- [ ] Si demora >5 min, revisa Vercel logs por errores

---

## Vercel: Verifica el Build Completó

En la línea del deployment en Vercel, haz click:

```
✅ Ready | 1m 34s | Git: [hash] | Branch: main
```

Se abre la página del deployment. Busca:

- [ ] Build duration: < 3 minutos (normal)
- [ ] Status: ✅ **Ready** (verde)
- [ ] Funciones: "Vercel Functions" ✅ (si las uses)
- [ ] No hay linea roja que diga "Failed" o "Error"

**Si ves errores:**
- [ ] Haz click en "Error" para ver logs
- [ ] Busca palabras clave: `SyntaxError`, `MODULE_NOT_FOUND`, `ENOENT`
- [ ] Si es un error conocido, consúltalo con el reviewer

---

## Live URL: Hard Refresh

Una vez que Vercel dice ✅ **Ready**, abre tu URL de producción:

```bash
# Abre en navegador
https://contexia.online/app/bunker
# O
https://[tu-proyecto].vercel.app

# Hard refresh (no cache)
# Windows/Linux: Ctrl+F5
# Mac: Cmd+Shift+R
```

Checklist:
- [ ] URL carga sin "Cannot GET" o 404
- [ ] La página no muestra versión antigua
- [ ] Cambios esperados son visibles
- [ ] Abre DevTools (F12) → Console → sin errores rojo

---

## Verificación Funcional

**Para cada cambio, verifica:**

Si era un cambio de **UI:**
- [ ] Nuevo componente se renderiza
- [ ] Estilos se aplican correctamente
- [ ] Inputs funcionan (no están deshabilitados)
- [ ] Navegación funciona

Si era un cambio de **API o lógica:**
- [ ] Endpoint responde con 200 (o status esperado)
- [ ] Response format matches spec.md
- [ ] Validación funciona (error cases)

---

## Rollback (Si Algo Salió Mal)

Si el cambio rompió algo:

```bash
# 1. Identifica tu commit
git log --oneline -5
# Busca el que hiciste

# 2. Deshazlo
git revert [commit-hash]
# (esto crea un nuevo commit que deshace tu cambio)

# 3. Push el revert
git push origin [branch]

# 4. Vercel desplegará automáticamente el revert
# Espera a que esté ✅ Ready
```

Checklist:
- [ ] `git revert` creó un commit nuevo
- [ ] Push del revert fue exitoso
- [ ] Vercel detectó el nuevo commit
- [ ] Vercel build completó ✅ Ready
- [ ] Abriste la URL de nuevo y el problema desapareció

---

## Reporte

```markdown
## Vercel Deployment — [CHANGE-ID]

- Commit: `[git rev-parse --short HEAD]`
- Vercel URL: https://vercel.com/contexia/[project]/deployments/[deployment-id]
- Build time: [X minutos]
- Status: ✅ READY

### Verificación en Vivo
- URL: https://[production-url]
- Cambios visibles: ✅ Sí
- No hay errores en console: ✅ Sí
```

Copia esto a:
```
openspec/changes/[CHANGE-ID]/reports/YYYY-MM-DD-vercel-deployment.md
```

---

## Troubleshooting Rápido

| Problema | Causa | Solución |
|----------|-------|----------|
| "Cannot GET /" | Build falló silenciosamente | Mira Vercel build logs |
| Page muestra versión antigua | Cache del navegador | Hard refresh (Ctrl+F5) |
| "Module not found" | Cambio falta en el push | `git push origin [branch]` de nuevo |
| Build tarda >10 min | Dependency installs lento | Revisa Vercel logs por network issues |
| Vercel no detectó commit | Push no llegó a remoto | `git push -v` para ver verbosity |

---

## Referencias

- Vercel docs: https://vercel.com/docs/deployments/overview
- antigravity-app Vercel project: https://vercel.com/contexia/antigravity-app
- contexia.online Vercel project: https://vercel.com/contexia/contexia
