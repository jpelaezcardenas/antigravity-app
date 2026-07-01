# ESTADO ACTUAL: Migración Keeper → Bitwarden

**Fecha:** 2026-06-15 17:00 UTC  
**Sesión:** Web Claude Code → OpenAI Codex (Academic Account)

---

## ✅ COMPLETADO

| Item | Ubicación | Status |
|------|-----------|--------|
| OpenSpec (spec, scenarios, tasks, README, dashboard) | `openspec/changes/keeper-migration-2026-06-15/` | ✅ |
| secrets_provider.py (abstracción provider) | `apps/backend/core/` | ✅ |
| secrets_endpoints.py (health check) | `apps/backend/api/endpoints/` | ✅ |
| docker-compose.vaultwarden.yml (Phase 2) | Repo root | ✅ |
| railway.vaultwarden.toml (Phase 2) | Repo root | ✅ |
| T1 Validation Report (330 secretos validados) | `openspec/changes/.../reports/T1-*` | ✅ |
| Git Commits (4 commits) | `ed8babd`, `177d2fc`, `0fe1153`, `cd19c79` | ✅ |

---

## ⏳ PENDIENTE (T2–T14)

**Próximo paso:** Juan inicia T2 (crear cuenta Bitwarden Cloud)

| Tarea | Dueño | Tiempo | Línea |
|-------|-------|--------|-------|
| T2: Bitwarden Cloud account | Juan | 20m | `CURSOR_PROMPT.md` → T2 section |
| T3: bw CLI install | Dev | 30m | `CURSOR_PROMPT.md` → T3 section |
| T4–T6: Import, organize, validate | Dev+Infra | 4h | `tasks.md` T4–T6 |
| T7–T9: Code + tests | Dev+QA | 6h | `tasks.md` T7–T9 |
| T10–T12: Railway + prod deploy | Dev+Infra | 2.5h | `tasks.md` T10–T12 |
| T13: Health audits | Infra+Dev | 1h | `tasks.md` T13 |
| T14: Delete Keeper | Juan | 30m | `tasks.md` T14 |

---

## 📂 ARCHIVOS CLAVE (LEE EN ESTE ORDEN)

1. **`CURSOR_PROMPT.md`** ← Empieza aquí (prompt simple para Cursor)
2. **`KEEPER_MIGRATION_HANDOFF.md`** ← Instrucciones detalladas T2–T14
3. **`openspec/changes/keeper-migration-2026-06-15/tasks.md`** ← Referencia cada tarea
4. **`openspec/changes/keeper-migration-2026-06-15/MIGRATION_DASHBOARD.md`** ← Timeline, gates, métricas

---

## 🚀 INICIO RÁPIDO (Cursor)

```bash
# Paso 1: Leer el prompt
cat CURSOR_PROMPT.md

# Paso 2: Hacer T2 (Juan, 20 min)
# (Crear cuenta Bitwarden Cloud)

# Paso 3: Hacer T3 (Dev, 30 min)
# (Instalar bw CLI)

# Paso 4: Seguir tasks.md para T4–T14
```

---

## 🎯 DECISIONES CRÍTICAS

| Gate | Cuándo | Qué Validar | Bloqueador |
|------|--------|-------------|-----------|
| **GATE 1** | Después de T6 | Todas las 6 API keys funcionan | Si falla: Scenario 2 (format invalid) |
| **GATE 2** | Después de T12 | Prod health check 200, sin refs a Keeper | Si falla: Scenario 5 (missing env vars) |
| **GATE 3** | Antes de T14 | T13 audits PASSED, backup listo | Si falla: NO delete Keeper (irreversible) |

---

## 📝 REGLAS IMPORTANTES

✅ **DO:**
- Leer `CURSOR_PROMPT.md` primero
- Actualizar `tasks.md` ANTES de codear (spec-first)
- Hacer commit después de cada tarea
- Seguir los gates de decisión

❌ **DON'T:**
- Skip OpenSpec validation
- Borrar Keeper antes de T13✅
- Dejar Keeper CSV export en disco (shred después de T4)
- Saltarse los gates de decisión

---

## 💬 SI TE ATASCAS

1. Abre `KEEPER_MIGRATION_HANDOFF.md` → "DEBUGGING CHECKLIST"
2. Busca el problema en `scenarios.md` → lee la mitigación
3. Contacta a Juan (Infra Lead) o Dev Team

---

## CUANDO VUELVAS A CLAUDE (con créditos)

Todo estará documentado así:
- ✅ Commits git con mensajes claros
- ✅ `MIGRATION_DASHBOARD.md` actualizado con progreso
- ✅ `reports/` carpeta con evidencia de cada T
- ✅ `tasks.md` actualizado con status

**No necesitarás re-explicar nada.** Solo:
1. Lee git log (últimos commits)
2. Lee MIGRATION_DASHBOARD.md (progreso)
3. Continúa con siguiente T pendiente

---

## GIT STATE

**Branch:** `fix/security-bug-audit-2026-06-14`  
**Last commit:** `cd19c79` (quick start guide)  
**Commits this session:** 4 (all documented)

```bash
# Ver último commit
git log --oneline -1

# Ver all commits de esta sesión
git log --oneline -4
```

---

## VALIDACIÓN FINAL (para Claude cuando vuelva)

Cuando regreses a Claude con créditos, solo necesitas:

```bash
# 1. Ver dónde estamos
git log --oneline -5
cat MIGRATION_DASHBOARD.md | grep "Status"

# 2. Ver qué quedó pendiente
cat openspec/changes/keeper-migration-2026-06-15/tasks.md | grep "⏳"

# 3. Continuar desde donde Cursor lo dejó
```

---

**Created:** 2026-06-15 17:00 UTC  
**For:** Claude (when returning with credits)  
**Status:** Ready to verify & close Phase 1
