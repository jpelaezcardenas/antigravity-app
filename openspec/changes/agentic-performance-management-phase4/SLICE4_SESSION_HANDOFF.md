# SLICE 4 SESSION HANDOFF — Iniciación para Nuevos Chats en Claude Code

**Fecha:** 2026-06-21  
**Sesión:** Slice 4 Tasks 4.1–4.3 completadas  
**Estado:** Ready for next chat (Slice 4.4 → Social Ops endpoints)

---

## 📋 RESUMEN EJECUTIVO

### ✅ Completado esta sesión

| Task | Descripción | Evidencia |
|------|-------------|-----------|
| 4.1 | Intent router: status→Pulso, risk→Radar | 4/4 tests GREEN |
| 4.2 | Fallback baja confianza: respuesta aclaratoria | 1/1 test GREEN |
| 4.3 | Escalación sensible: approval_queue taty_escalation | 1/1 test GREEN |

**Totales:**
- **6/6 tests Taty** (100% GREEN)
- **88/88 suite backend** (↑2 desde sesión anterior, 0 regresiones)
- **49 skipped, 4 pre-existing failures** (passlib — no relacionado)

### 🎯 Próximo paso
**Task 4.4–4.5:** Social Ops endpoints FastAPI (Content Ideas, Lead Reply, Sales Closure, Metrics Analyzer) behind `social_ops_canonical` feature flag.

---

## 🚀 CÓMO INICIAR UN NUEVO CHAT EN CLAUDE CODE

### Paso 1: Copiar este prompt de contexto (COPIA EXACTAMENTE)

```
Contexto previo: Acabo de completar Slice 4 Tasks 4.1–4.3 de FASE 4 (Agentic Performance Management):

✅ COMPLETADO:
- 4.1: Intent router para Taty (status→Pulso, risk→Radar)
- 4.2: Fallback de baja confianza (respuesta aclaratoria, sin agentes)
- 4.3: Escalación de intents sensibles a approval_queue con draft_type='taty_escalation'

✅ VERIFICACIÓN:
- 6/6 tests Taty GREEN
- 88/88 suite backend (0 regresiones)
- Cero fallos nuevos

📁 ARCHIVOS EDITADOS/CREADOS:
- services/taty_intent_router.py (new)
- tests/test_taty_intent_router.py (new)
- openspec/changes/agentic-performance-management-phase4/tasks.md (updated 4.1, 4.2, 4.3)

🔗 REFERENCIAS CRÍTICAS:
- Plan completo: openspec/changes/agentic-performance-management-phase4/tasks.md
- Spec Taty: openspec/changes/agentic-performance-management-phase4/specs/taty-conversational/spec.md
- Design Phase 4: openspec/changes/agentic-performance-management-phase4/design.md
- Hermes Workspace config: .hermes/profiles/contexia/config.yaml

PRÓXIMO: Task 4.4–4.5 (Social Ops endpoints FastAPI) — sigue TDD + OpenSpec.
```

### Paso 2: Ejecutar en el nuevo chat

```bash
# Verificar que estás en la rama correcta
git branch -v

# Verificar estado de tasks.md
grep "^- \[x\] 4\.[1-3\]" openspec/changes/agentic-performance-management-phase4/tasks.md

# Confirmar suite tests (86+88 should match)
cd apps/backend && python -m pytest tests/test_taty_intent_router.py -v --tb=short
```

---

## 🛠️ HERRAMIENTAS Y SCRIPTS NECESARIOS

### Environment Setup
```bash
# Verificar Python + venv activo
python --version
which python  # debe apuntar a .hermes/hermes-agent/venv/bin/python

# Instalar dependencias (si falta algo)
cd apps/backend
pip install -r requirements.txt
```

### Git Workflow (TDD + OpenSpec)
```bash
# Checkout rama main (siempre)
git checkout main
git pull origin main

# Crear rama de trabajo (NO la hagas, déjala en main)
# OpenSpec ya maneja branches de feature

# Status antes de empezar
git status
git log --oneline -5

# Al terminar cambios: TDD first, then git
# 1. Write test (RED)
pytest tests/test_*.py -v
# 2. Implement code (GREEN)
pytest tests/test_*.py -v
# 3. Verify suite (0 regressions)
pytest tests/ -q --ignore=tests/test_auth_deps.py --ignore=tests/test_social_ops_endpoints.py
# 4. Update tasks.md (MANDATORY)
# 5. Commit + push (AFTER verification)
```

### Test Execution (Patterns)

**Individual test file:**
```bash
cd apps/backend && python -m pytest tests/test_taty_intent_router.py -v
```

**Full suite (ignoring known failures):**
```bash
cd apps/backend && python -m pytest tests/ -q \
  --ignore=tests/test_auth_deps.py \
  --ignore=tests/test_social_ops_endpoints.py
```

**Watch test results in real-time:**
```bash
# Run in background, then read output file when done
cd apps/backend && python -m pytest tests/ -q \
  --ignore=tests/test_auth_deps.py \
  --ignore=tests/test_social_ops_endpoints.py 2>&1 | tail -5
```

---

## 📚 ESTRUCTURA OPENSPEC (OBLIGATORIA)

### Archivos Críticos por Orden

1. **tasks.md** — Fuente de verdad
   - Ubicación: `openspec/changes/agentic-performance-management-phase4/tasks.md`
   - **SIEMPRE actualiza cuando completes un task** (marca `[x]` + descripción)
   - Formato: `- [x] TASK_NUM descripción — implementación detalles`

2. **design.md** — Contexto arquitectónico
   - Ubicación: `openspec/changes/agentic-performance-management-phase4/design.md`
   - No edites a menos que cambie la arquitectura fundamental

3. **specs/** — Spec por agente/componente
   - `specs/taty-conversational/spec.md` — Taty requirements (LEER ANTES DE 4.4)
   - `specs/social-ops-canonical/` — Social Ops requirements (PARA 4.4+)

4. **reports/** — Deployment reports (Stage 11)
   - Solo crear DESPUÉS de deploy a production
   - Formato: `YYYY-MM-DD-slice-N-deployment.md`

### Flujo OpenSpec OBLIGATORIO para Nueva Tarea

Antes de escribir CUALQUIER código:

```
1. READ tasks.md → identifica task número (ej. 4.4)
2. READ spec correspondiente (ej. specs/social-ops-canonical/spec.md)
3. READ design.md → entiende arquitectura
4. WRITE failing test (TDD — RED)
5. IMPLEMENT código mínimo (GREEN)
6. VERIFY suite (0 regresiones)
7. UPDATE tasks.md con evidencia
8. GIT COMMIT con descripción clara
9. (Stage 11 solo) DEPLOY + write report
```

---

## 🔑 CONTEXTO PROYECTO

### Identidad Contexia
- **Entidad técnica:** Contexia SAS (IA + Fintech)
- **Cliente Cero:** NIT 900000000 (`tenants.is_cliente_cero = true`)
- **Dominio:** Automatización fiscal + DIAN compliance

### FASE 4: Agentic Performance Management

**Objetivo:** 9 agentes autónomos (Centinela, Pulso, Radar, Auditoría, Taty, Social Ops x4, Maestro) coordinados vía Hermes Workspace.

**Slices:**
- **Slice 1** ✅ — Shadow GL schema
- **Slice 2** ✅ — Centinela + Approval Queue
- **Slice 3** ✅ — Pulso + Radar + Auditoría
- **Slice 4** 🟡 — **Taty (4.1–4.3 ✅, 4.4+ 📋) + Social Ops**
- **Slice 5** ⬜ — Maestro + KB integration

### Tech Stack

| Componente | Tech |
|-----------|------|
| Backend | FastAPI + Python |
| DB | Supabase (PostgreSQL + pgvector) |
| LLM | Groq (llama-4-scout-17b, 30K TPM) |
| Deploy | Railway (antigravity-app-production-175a) |
| Frontend | React (Vercel, contexia.online/app/bunker) |
| Local Dev | Hermes Workspace (localhost:3000) |

---

## 📍 REFERENCIAS CRÍTICAS POR TIPO DE TAREA

### Para Task 4.4–4.5 (Social Ops endpoints)

**Files to read FIRST:**
- `specs/social-ops-canonical/spec.md` — requirements
- `tasks.md` líneas 50–52 — task descriptions
- `services/approval_queue_service.py` — patrón enqueue_draft
- `presentation/*_endpoints.py` — patrón para nuevos routers

**Pattern to follow (copia de Slice 3):**
1. Service layer: `services/social_ops_service.py` (Content, Lead Reply, etc.)
2. Endpoints layer: `presentation/social_ops_endpoints.py`
3. Tests: `tests/test_social_ops_service.py` + `tests/test_social_ops_endpoints.py`
4. Feature flag: `apps/backend/config.py` → `SOCIAL_OPS_CANONICAL` (default False)
5. Router mount: `presentation/router.py` → include_router con condition

**Tests MUST mock:**
- `approval_queue_service.enqueue_draft` (sin tocar DB real)
- LLM cascade (usar fixture de respuesta)
- n8n equivalent (si aplica)

### Para Task 4.6–4.7 (Parallel-run flag test)

**What to monitor:**
- n8n logs vs FastAPI logs
- approval_queue entries (n8n: 0, FastAPI: N)
- Feature flag flip criteria (message match % > 95%)

**Rollback plan:**
- `SOCIAL_OPS_CANONICAL = False` → revierte a n8n

---

## 🎯 CHECKLIST PARA INICIAR NUEVO CHAT

### Pre-Chat Checklist

- [ ] Copié el **prompt de contexto** (sección "Paso 1")
- [ ] Verifiqué que estoy en rama `main`
- [ ] Leí `tasks.md` línea del próximo task
- [ ] Leí spec correspondiente (ej. `specs/social-ops-canonical/spec.md`)
- [ ] Verifiqué `git status` limpio o documenté cambios pendientes

### In-Chat Checklist (después de copiar contexto)

1. **Confirmación inicial:**
   - [ ] Pegué el prompt de contexto
   - [ ] Me confirmó que entiende dónde estamos (4.1–4.3 done, 4.4 next)
   - [ ] Verificó `git branch -v` y `git log --oneline -5`

2. **Task Execution:**
   - [ ] Leí el spec del task (RED → GREEN → Suite → Update tasks.md)
   - [ ] Escribí test que falla (RED)
   - [ ] Implementé código mínimo (GREEN)
   - [ ] Corrí suite completa (0 regressions)
   - [ ] Actualicé `tasks.md` con evidencia

3. **Commit & Push:**
   - [ ] `git diff` reviewed
   - [ ] `git status` sin archivos no deseados (.env, __pycache__, etc.)
   - [ ] `git commit` con mensaje claro
   - [ ] `git push origin main` (o rama feature si OpenSpec lo requiere)

4. **Stage 11 (solo si es deploy):**
   - [ ] Railway deploy verificado (status verde)
   - [ ] Production URL accesible
   - [ ] Endpoints responden 200 OK con datos reales
   - [ ] Deployment report creado: `reports/YYYY-MM-DD-slice-N-deployment.md`

---

## 🔗 ARCHIVOS CLAVE (LECTURA OBLIGATORIA)

### Documentos principales
- `openspec/changes/agentic-performance-management-phase4/` — raíz del cambio
  - `tasks.md` — fuente de verdad
  - `design.md` — arquitectura
  - `proposal.md` — justificación del cambio
  - `specs/` — specs por componente
  - `reports/` — deployment reports

### Código referencia (patrones)
- `apps/backend/services/pulso_diario_service.py` — patrón service (Slice 3)
- `apps/backend/services/radar_service.py` — patrón con HITL gate
- `apps/backend/services/approval_queue_service.py` — patrón enqueue + approve
- `apps/backend/presentation/pulso_diario_endpoints.py` — patrón endpoints
- `apps/backend/tests/test_taty_intent_router.py` — TDD test pattern

### Config
- `.hermes/profiles/contexia/config.yaml` — Hermes Agent config (WSL)
- `apps/backend/config.py` — Feature flags (SOCIAL_OPS_CANONICAL)
- `openspec/changes/agentic-performance-management-phase4/.openspec.yaml` — OpenSpec meta

---

## 🚨 GOTCHAS & TROUBLESHOOTING

### Test Failures
- **passlib ImportError:** Pre-existing gap desde Slice 2. Ignora con `--ignore=tests/test_auth_deps.py --ignore=tests/test_social_ops_endpoints.py`
- **Supabase RLS errors:** Asegúrate de que las migrations se aplicaron. Lee `reports/` de slices previos.
- **Groq 429 (rate limit):** Normal — Groq free tier tiene 30 TPM. El test fallará si corres demasiado en paralelo. Espera unos segundos entre test runs.

### Git Issues
- **Uncommitted changes:** Corre `git status` antes de cambiar rama. No dejes cambios sin commit.
- **Branch tracking:** Verifica con `git branch -vv` que tracks `origin/main`.
- **Merge conflicts:** Improbable si siempre checkout `main` limpio. Si ocurre, resuelve manualmente y commit.

### Hermes Workspace (local)
- **Gateway no responde:** `curl http://127.0.0.1:8642/health` debe devolver `{"status": "ok"}`. Si no, reinicia el WSL gateway.
- **Workspace 3000 muestra "Welcome":** Hard refresh (Ctrl+Shift+R) + clear localStorage.
- **Token issues:** Verifica `.env` en `hermes-workspace/` tiene `HERMES_API_TOKEN=contexia-dev-token-123`.

---

## 📞 CONTACTO & REFERENCIAS

### Dentro del proyecto
- **Dirección técnica:** Ver `.antigravity/GROUND_TRUTH.md`
- **OpenSpec docs:** `ai-specs/openspec-deployment-standard/`
- **Hermes docs:** `hermes-workspace/docs/`

### External (si cuelgas)
- **DIAN compliance:** Via Contexia legal team
- **Siigo integration:** Blocked on sandbox credentials (design.md Open Questions)
- **Telegram bot token:** Already provisioned (@contexia_bot)

---

## 🎬 PRIMER COMANDO EN NUEVO CHAT

```bash
# Pega esto en tu primer bash:
cd /c/Users/contexia/Projects/antigravity-app/apps/backend && \
git status && \
git log --oneline -5 && \
python -m pytest tests/test_taty_intent_router.py -v --tb=short | tail -20
```

**Salida esperada:**
- `On branch main`
- Last 5 commits incluyen tasks Slice 3 + 4.1–4.3
- `6 passed in ...` (Taty tests GREEN)

---

## ✅ SESSION COMPLETE

**Estado final:**
- ✅ Slice 4 Tasks 4.1–4.3 completadas
- ✅ 6/6 Taty tests GREEN
- ✅ 88/88 suite backend (0 regressions)
- ✅ tasks.md actualizado con evidencia
- ✅ Handoff document listo para siguiente chat

**Siguiente sesión:**
- Task 4.4–4.5: Social Ops endpoints FastAPI
- Sigue TDD + OpenSpec sin variaciones
- Expected duration: 1–2 horas (similar a Slice 4.1–4.3)

---

**Preparado por:** Claude Code  
**Timestamp:** 2026-06-21 21:30 UTC  
**Para:** Próximo chat Claude Code (Slice 4.4+)
