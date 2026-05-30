# OpenSpec + Deployment Standard — Setup & Execution Guide

**Versión:** 1.0  
**Fecha:** 2026-05-30  
**Aplica a:** Todos los 8 proyectos en Contexia + 4 plataformas de desarrollo

---

## 📋 Resumen Ejecutivo

**Problema:** OpenSpec archivaba tareas pero cambios NO llegaban a producción.  
**Solución:** Implementé **Stage 11: Deploy to Production** como paso obligatorio.

**Resultado:**
```
OpenSpec tradicional:
  proposal → design → spec → tasks → apply → archive
  
Con este estándar:
  proposal → design → spec → tasks → apply → [DEPLOY & VERIFY] → archive
```

---

## 🚀 Fase 1: Validación (5 min)

Verifica que los archivos se crearon correctamente:

```bash
cd C:\Users\contexia\Projects

# Verifica que ai-specs/openspec-deployment-standard/ existe
ls -la ai-specs/openspec-deployment-standard/
# Debería mostrar: DEPLOYMENT_STAGE.md, CHECKPOINTS.md, etc.

# Verifica que archivos de plataforma existen
ls -la ~/.antigravity/CLAUDE.md
ls -la ~/.antigravity2/CLAUDE.md
ls -la ai-specs/codex-context.md
```

**Si todo aparece:** ✅ Fase 1 completada.

---

## 📌 Fase 2: Antigravity-App POC (10 min)

Crea symlink y verifica:

```bash
cd antigravity-app

# 1. Crea symlink a deployment standard
ln -s ../ai-specs/openspec-deployment-standard DEPLOYMENT_STAGE

# 2. Verifica que el symlink funciona
ls -la DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md
# Debería mostrar: → ../ai-specs/openspec-deployment-standard/DEPLOYMENT_STAGE.md

# 3. Verifica que CLAUDE.md tiene sección 8 (Stage 11)
grep -A 5 "Deployment Stage" CLAUDE.md
# Debería mostrar la nueva sección

# 4. Haz git add
git add CLAUDE.md
git status --short
```

**Si todo funciona:** ✅ Fase 2 completada. Antigravity-app está configurado.

---

## 📦 Fase 3: Replicar a Otros 7 Proyectos (35 min)

Para **cada proyecto** (repite estos comandos):

```bash
cd contexia-app-stitch          # (reemplaza con cada proyecto)

# 1. Crea symlink
ln -s ../ai-specs/openspec-deployment-standard DEPLOYMENT_STAGE

# 2. Verifica symlink
ls -la DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md

# 3. Actualiza CLAUDE.md (copia la sección Stage 11 de antigravity-app)
# Opción manual: abre CLAUDE.md y pega sección 8 al final
# Opción rápida: copia el contenido de antigravity-app/CLAUDE.md

# 4. Git add
git add CLAUDE.md
```

**Proyectos a actualizar:**
1. antigravity-app-taty-fiscal-telegram-rag (removido 2026-05-30)
2. ~~contexia-app-stitch~~ (removido 2026-05-30 — no en uso)
3. contexia-landing-deploy
4. contexia-ops-template
5. ~~contexia-social-ops~~ (removido 2026-05-30 — era worktree redundante)
6. copiloto-contratos-eafit
7. ~~temp_pwa~~ (removido 2026-05-30 — sin código, no en uso)

**Tracking:** Usa tabla abajo para marcar progreso.

---

## ✅ Fase 4: Validación Global (15 min)

```bash
cd C:\Users\contexia\Projects

# Valida todos los symlinks
for dir in antigravity-app contexia-landing-deploy contexia-ops-template copiloto-contratos-eafit; do
  if [ -L "$dir/DEPLOYMENT_STAGE" ]; then
    echo "✅ $dir"
  else
    echo "❌ $dir NEEDS SYMLINK"
  fi
done

# Valida que CLAUDE.md tiene Stage 11 en cada proyecto
for dir in antigravity-app; do
  echo "=== $dir ==="
  grep "Stage 11" "$dir/CLAUDE.md" | head -1
done
```

**Si todos tienen ✅:** Fase 4 completada.

---

## 📝 Fase 5: Git Commit Global (5 min)

```bash
cd C:\Users\contexia\Projects

# 1. Stage everything
git add ai-specs/openspec-deployment-standard/
git add .antigravity/CLAUDE.md .antigravity2/CLAUDE.md
git add ai-specs/codex-context.md
git add **/CLAUDE.md  # Todos los CLAUDE.md actualizados
git add ~/.claude/MEMORY.md

# 2. Verifica qué vas a commitear
git status --short | head -20

# 3. Commit
git commit -m "feat: openspec deployment standard for all projects

- Created ai-specs/openspec-deployment-standard/ with:
  - DEPLOYMENT_STAGE.md: full 11-step workflow
  - CHECKPOINTS.md: objective criteria + self-improving loop
  - checklist-vercel.md: frontend deployment
  - checklist-railway.md: backend deployment
  - INTEGRATION_GUIDE.md: how to apply
  - README.md: this guide

- Applied to all 8 projects:
  - Created symlinks (DEPLOYMENT_STAGE/)
  - Updated CLAUDE.md (Stage 11 section)
  
- Created platform-specific configs:
  - .antigravity/CLAUDE.md (Antigravity IDE)
  - .antigravity2/CLAUDE.md (Antigravity 2.0)
  - ai-specs/codex-context.md (Codex context)

- Updated global:
  - .claude/MEMORY.md (tracking)

Closes the gap: OpenSpec archive now includes mandatory Stage 11.
Self-improving loop: CHECKPOINTS.md evolves based on reviewer feedback."

# 4. Push
git push origin main
```

**Si push es exitoso:** ✅ Fase 5 completada.

---

## 🧪 Fase 6: Test (Primera Implementación)

**Cuándo:** Cuando próximas tareas lleguen a antigravity-app.

**Qué hacer:**
1. Abre una OpenSpec change (nueva o existente)
2. Lee `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md` completo
3. Si la change no tiene Stage 11 en tasks.md, añádelo
4. Ejecuta todos los tasks incluyendo Stage 11
5. Crea deployment report (screenshots, logs, etc.)
6. Archiva la change

**Resultado esperado:**
- ✅ Cambios visibles en https://contexia.online/app/bunker
- ✅ Reporte existe en openspec/changes/[CHANGE-ID]/reports/
- ✅ CHECKPOINTS.md está listo para mejorar

---

## 📊 Tracking Table

Marca cada proyecto conforme completes las fases:

| Proyecto | Symlink | CLAUDE.md | Verified | Status |
|----------|---------|-----------|----------|--------|
| antigravity-app | ✅ | ✅ | ✅ | POC |
| antigravity-app-taty-fiscal-telegram-rag | ~~[ ]~~ | ~~[ ]~~ | ~~[ ]~~ | REMOVED 2026-05-30 |
| ~~contexia-app-stitch~~ | — | — | — | REMOVED 2026-05-30 (no longer in use) |
| contexia-landing-deploy | [ ] | [ ] | [ ] | Ready |
| contexia-ops-template | [ ] | [ ] | [ ] | Ready |
| ~~contexia-social-ops~~ | — | — | — | REMOVED 2026-05-30 (redundant worktree) |
| copiloto-contratos-eafit | [ ] | [ ] | [ ] | Ready |
| ~~temp_pwa~~ | — | — | — | REMOVED 2026-05-30 (unused PWA, no code) |

---

## 🆘 Troubleshooting Setup

| Problema | Solución |
|----------|----------|
| Symlink no funciona (Windows) | Usa `mklink /d DEPLOYMENT_STAGE ..\ai-specs\openspec-deployment-standard` en PowerShell |
| CLAUDE.md duplicado en diferentes ubicaciones | Centraliza en ai-specs/, usa symlinks desde .claude/ y .cursor/ |
| Git no ve DEPLOYMENT_STAGE/ | Symlinks en git: `git config core.symlinks true` |
| Merge conflict en CLAUDE.md | Resuelve manualmente: Stage 11 va al final antes del cierre |

---

## 📱 Plataformas de Desarrollo

### Claude Code
- ✅ Configurado via `.claude/CLAUDE.md` en cada proyecto
- Carga automáticamente la sección Stage 11

### Antigravity IDE
- ✅ Nuevo: `.antigravity/CLAUDE.md` con instrucciones específicas
- Usa integrated terminal para git push

### Antigravity 2.0
- ✅ Nuevo: `.antigravity2/CLAUDE.md` con enhanced workflows
- Soporta multi-project + live reload

### Codex (ChatGPT)
- ✅ Nuevo: `ai-specs/codex-context.md`
- Pega al inicio de cada chat Codex

---

## 📚 Key Files

| Archivo | Propósito | Cuándo Usar |
|---------|-----------|------------|
| DEPLOYMENT_STAGE.md | Full workflow (11 steps) | Lees para entender todo |
| CHECKPOINTS.md | Objective criteria + loop | Referee valida contra esto |
| checklist-vercel.md | Frontend deployment steps | Si cambio es UI |
| checklist-railway.md | Backend deployment steps | Si cambio es API/DB |
| INTEGRATION_GUIDE.md | Cómo instalar en proyectos | Una sola vez (ya está hecho) |
| README.md | Este archivo | Referencia general |

---

## 🔄 Self-Improving Loop (En Acción)

**Semana 1-2:** Primer deployment con Stage 11
- Algunos pasos pueden fallar
- Documenta cada error nuevo

**Semana 2-3:** Reviewer añade criterios a CHECKPOINTS.md
- "Verifica env vars antes de push"
- "Hard refresh es obligatorio"
- Etc.

**Semana 3+:** Próximos developers heredan esas reglas
- No repiten errores anteriores
- CHECKPOINTS.md evoluciona
- En 2-3 meses, es una gema de knowledge

---

## ✨ Success Criteria

Sabrás que está listo cuando:

- [ ] Todos los symlinks funcionan (8 proyectos)
- [ ] Todos los CLAUDE.md tienen sección Stage 11 (8 proyectos)
- [ ] Antigravity-app hace git push sin errores
- [ ] Vercel y Railway configs están en CLAUDE.md
- [ ] Primera change es deployada y reportada
- [ ] CHECKPOINTS.md tiene ≥ 15 criterios objetivos

---

## 🎯 Próximos Pasos (Post-Setup)

1. **Semana 1:** Antigravity-app: próximo change con Stage 11 completo
2. **Semana 2:** Test deployment real (Vercel + Railway)
3. **Semana 2-3:** Otros 7 proyectos: un change cada uno
4. **Semana 3+:** Self-improving loop retroalimenta CHECKPOINTS.md
5. **Mes 2-3:** CHECKPOINTS.md es resumen brutal de expertise

---

## 📞 Contacto / Preguntas

Si algo falla y no está en CHECKPOINTS.md:
1. Documenta el error exacto
2. El reviewer lo añade a CHECKPOINTS.md
3. Próximo developer hereda esa regla

El sistema se auto-repara.

---

**Created:** 2026-05-30  
**Status:** ✅ Ready for Implementation  
**Version:** 1.0
