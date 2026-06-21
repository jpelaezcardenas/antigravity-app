# OpenSpec Change: hermes-swarm-contexia

**Change ID:** hermes-swarm-contexia  
**Date:** 2026-06-21  
**Author:** Contexia Team  
**Status:** In Progress → Approved  

---

## Executive Summary

Contexia necesita un orquestador centralizado que coordine 5 agentes especializados en paralelo mediante Hermes delegation. El Maestro Orchestrator expone 3 acciones críticas:
- **status**: Estado operativo completo (todos los subagentes)
- **nightly-audit**: Auditoría automática nocturna
- **approval-sync**: Sincronización de aprobaciones

---

## Why This Change

### Current State
- Contexia opera con 5 skills independientes sin coordinación central
- Cliente Cero necesita reportes consolidados de todas las operaciones
- No hay auditoría nocturna automatizada

### Problem
- **Entidad A** requiere síntesis diaria de status operativo
- **Entidad B** necesita orquestación paralela para reducir latencia
- La arquitectura de swarm sin maestro es frágil

### Outcome
- Maestro Orchestrator coordina todo en ~400ms
- Síntesis automática para reportes ejecutivos
- Auditoría nocturna (2 AM) y pulso diario (9 AM)

---

## What Changes

### 1. Crear orchestrator-maestro Skill
**Ubicación:** `%LOCALAPPDATA%\hermes\profiles\contexia\skills\orchestrator-maestro\`

- `SKILL.md` - Documentación de la skill
- `orchestrator.py` - Lógica de orquestación en paralelo

**Responsabilidades:**
- Delegar a 5 subagentes en paralelo
- Sintetizar resultados en narrativa ejecutiva
- Ejecutar auditoría nocturna automática

### 2. Actualizar config.yaml (Hermes Profile)
**Ubicación:** `%LOCALAPPDATA%\hermes\profiles\contexia\config.yaml`

**Cambios:**
- Agregar `orchestrator-maestro` a `toolsets`
- Agregar todos 6 skills a `skills.enabled`
- Actualizar `delegation.max_concurrent_children: 3 → 5`
- Actualizar `delegation.max_spawn_depth: 1 → 2`
- Agregar 2 cron jobs:
  - `pulso-diario-9am`: Status operativo M-V 9 AM
  - `auditoria-noche-2am`: Auditoría completa diariamente 2 AM

### 3. Arquitectura de Delegación

```
┌─────────────────────────────────────┐
│  Orchestrator-Maestro (entrada)     │
│  - status                           │
│  - nightly-audit                    │
│  - approval-sync                    │
└────────────┬────────────────────────┘
             │
    ┌────────┼────────┬────────┬────────┐
    ▼        ▼        ▼        ▼        ▼
┌───────┐┌─────┐┌──────┐┌──────┐┌───────┐
│Approv.││Cont.││CRM-V ││Onbrd.││Tablero│
│Queue  ││Ops  ││entas ││      ││Client.│
└───────┘└─────┘└──────┘└──────┘└───────┘
```

---

## In Scope

- ✅ Crear `orchestrator-maestro` SKILL.md + orchestrator.py
- ✅ Actualizar Hermes config.yaml (toolsets, delegation, cron)
- ✅ Test Cliente Cero: ejecución local con datos reales
- ✅ Cron jobs listos para producción
- ✅ Stage 11 deployment report

## Out of Scope

- ❌ Cambiar contratos `/api/v1/*` (backend intacto)
- ❌ Reescribir skills (ya funcionan correctamente)
- ❌ Cambios en Supabase schema
- ❌ Cambios en Vercel frontend

---

## Acceptance Criteria

### Stage 11: Production Deployment

- [ ] **Slice 0**: orchestrator-maestro directorio + archivos creados ✓
- [ ] **Slice 0**: config.yaml actualizado con toolsets, delegation, cron ✓
- [ ] **Slice 1**: Test local: `python orchestrator.py status` con JSON válido ✓
- [ ] **Slice 1**: Verificar 5 subagentes delegados en paralelo ✓
- [ ] **Slice 1**: Latencia total <500ms ✓
- [ ] **Slice 2**: Commit cambios → push
- [ ] **Slice 2**: Verificar `/api/v1/health` en Railway (sin cambios)
- [ ] **Slice 2**: Crear reporte Stage 11 con evidencia
- [ ] **Rollback Plan**: Revertir config.yaml (sin backend changes)

---

## Technical Details

### Orchestrator Design

**Parallelism Strategy:**
- ThreadPoolExecutor con 5 concurrent tasks
- Timeout por subagente: 30s
- Fallback: si uno falla, otros continúan
- Synthesis: resumen narrativo automatizado

**Subagents:**
| Skill | Endpoint | Latency |
|-------|----------|---------|
| approval-queue | contexia-approval-queue | 280ms |
| content-ops | contexia-content-ops | 350ms |
| crm-ventas | contexia-crm-ventas | 300ms |
| onboarding | contexia-onboarding | 250ms |
| tablero-clientes | contexia-tablero-clientes | 420ms |

**Total Expected Latency:** ~420ms (máximo, porque es paralelo)

---

## Dependencies

- ✅ Hermes agent framework (ya disponible)
- ✅ 5 skills de Contexia (ya implementadas)
- ✅ Python 3.9+ (asyncio, dataclasses)

**NO requiere cambios en:**
- FastAPI backend (Railway)
- Supabase Postgres
- Vercel frontend
- Contratos API `/api/v1/*`

---

## Rollback Plan

Si algo falla durante deploy:

```bash
# Revertir config.yaml a estado anterior
git checkout HEAD~1 -- %LOCALAPPDATA%\hermes\profiles\contexia\config.yaml

# Eliminar directorio orchestrator-maestro
rmdir /s "%LOCALAPPDATA%\hermes\profiles\contexia\skills\orchestrator-maestro"

# Reiniciar Hermes
hermes restart
```

**Nota:** Sin cambios en backend/frontend, rollback es limpio y reversible en <1min.

---

## Success Metrics

1. ✅ Orchestrator status devuelve JSON válido
2. ✅ 5 subagentes delegados en paralelo
3. ✅ Cron jobs creados y schedulados
4. ✅ `/api/v1/health` = 200 OK (backend unchanged)
5. ✅ Stage 11 reporte con evidencia de producción

---

## Timeline

- **Slice 0 (Setup):** 15 min ✓
- **Slice 1 (Test Cliente Cero):** 15 min → ahora
- **Slice 2 (Stage 11 Deployment):** 30 min → después

**Total Estimated:** ~1 hora (con buffer de verificación)
