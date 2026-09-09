# Sesión activa

> El líder escribe aquí el plan vivo de la sesión. Los subagentes NO escriben aquí
> su detalle — eso va a `progress/impl_<id>.md` y `progress/review_<id>.md`.
> Al cerrar sesión: mover el resumen a `history.md` y dejar esta plantilla limpia.

**Actualizado:** 2026-09-09

**Último change cerrado (Stage 11 100% completo, listo para archivar):**
`whatsapp-b2b-lead-bridge` — 37/37 tareas en verde (Grupos 1-6 + Stage 11 completo). Commit
`75ae6e0`, merge con `origin/main` en `73f781e`, push a `main`. Migración
`0049_crm_leads_lead_type.sql` aplicada en Supabase y verificada en vivo. Railway deploy
`79eb9162` SUCCESS. **Verificación E2E confirmada con conversación real de WhatsApp** (el
fundador reinició el bridge local y probó en vivo): `crm_leads` de `573504187902` quedó con
`lead_type="business_interest"` tras el mensaje real "tengo empresa ya constituida...", sin
tocar `stage`, y un mensaje normal de Renta Natural en la misma conversación no lo activó. Ver
`openspec/changes/whatsapp-b2b-lead-bridge/reports/2026-09-09-deployment.md`.

**Decisión de diseño abierta, no bloqueante:** el mapeo semántico de `business_interest` a
`servicio_interes` usó `"creacion_empresa"` en vez de `"CFO"` (ambos son valores reales y
confirmados en la instancia de Chatwoot) — es un cambio de una línea en
`apps/chatwoot-bridge/main.py::_INTENT_TO_SERVICIO_INTERES` si la práctica real muestra que
`"CFO"` encaja mejor.

**Changes pendientes de implementación (en `openspec/changes/`, sin archivar):**

| Change | Estado | Prioridad estimada |
|---|---|---|
| `whatsapp-b2b-lead-bridge` | Stage 11 100% completo y verificado con prueba real | Archivar con `openspec-archive-change` |
| `taty-wompi-link-hitl-gate` | Pendiente — todas las tareas `[ ]` | Alta (bloquea cobros reales vía Wompi) |
| `metrics-dashboard-phase9` | Pendiente — todas las tareas `[ ]` | Media (dashboard de métricas internas) |
| `voicebox-local-voice-adoption` | Pendiente — todas las tareas `[ ]` | Baja (dark launch, requiere consentimiento de Tatiana) |
| `real-data-ingestion-mvp` | Bug de migración 0046 corregido en otra sesión paralela sin commitear todavía; resto de tracks completos | Revisar working tree antes de commitear |

**Acciones del fundador pendientes (no bloquean, pero deberían resolverse):**
- Verificación E2E con cliente B2B real en `/api/v1/agents/ask` (de `taty-per-tenant-profiles`)
- Activar `HERMES_BRIDGE_TOKEN` en Hermes + Railway (de `hermes-task-queue-tenant-scoping`)
- Merchant-of-record Wompi (task 5.1 de `taty-wompi-link-hitl-gate`, prerequisito para cerrar cobros)
- (Resuelto 2026-09-09) Prueba real por WhatsApp + reinicio del bridge local — confirmado en producción

**Estado:** sin tarea de implementación en curso. `whatsapp-b2b-lead-bridge` desplegado y
verificado hasta donde este harness puede alcanzar; queda a un paso de archivarse.
**Bloqueos:** hay archivos modificados/sin trackear en el working tree que NO pertenecen a este
change (`apps/backend/core/plan_features.py`, `apps/backend/migrations/0046_gmail_sender_map.sql`,
`apps/hermes-hubspot-poller/*`, `openspec/changes/real-data-ingestion-mvp/tasks.md`,
`ai-specs/references/`) — no fueron tocados por esta sesión; parecen de trabajo previo/paralelo sin
commitear. Revisar antes de cualquier commit para no mezclar cambios de distintos changes.
