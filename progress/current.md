# Sesión activa

> El líder escribe aquí el plan vivo de la sesión. Los subagentes NO escriben aquí
> su detalle — eso va a `progress/impl_<id>.md` y `progress/review_<id>.md`.
> Al cerrar sesión: mover el resumen a `history.md` y dejar esta plantilla limpia.

**Actualizado:** 2026-09-09

**Último change implementado:** `whatsapp-b2b-lead-bridge` — Grupos 1-6 (32/37 tareas) en verde,
revisados leader→implementer→reviewer, todos APPROVED. Ver `progress/history.md` (entrada
2026-09-09) para el resumen completo. NO commiteado, NO pusheado, NO desplegado. Migración
`0049_crm_leads_lead_type.sql` escrita pero NO aplicada.

**Bloqueado en el fundador (Stage 11 de `whatsapp-b2b-lead-bridge`):**
1. Aplicar migración `0049_crm_leads_lead_type.sql` en Supabase — requiere confirmación explícita.
2. `git commit` + `push` a `main` (deploy branch) — sin esto no hay cambio en producción.
3. Verificar deploy Railway.
4. Verificación E2E: conversación real/simulada de WhatsApp con lenguaje de negocio debe resultar
   en `crm_leads.lead_type` seteado + atributos Chatwoot correctos (`servicio_interes=
   creacion_empresa`, `tipo_contribuyente=SAS`), SIN cambiar el comportamiento de una conversación
   Renta Natural normal enviada inmediatamente después en la misma pasada de verificación.
5. Crear reporte `openspec/changes/whatsapp-b2b-lead-bridge/reports/YYYY-MM-DD-deployment.md`.

**Decisión de diseño abierta, no bloqueante:** el mapeo semántico de `business_interest` a
`servicio_interes` usó `"creacion_empresa"` en vez de `"CFO"` (ambos son valores reales y
confirmados en la instancia de Chatwoot) — es un cambio de una línea en
`apps/chatwoot-bridge/main.py::_INTENT_TO_SERVICIO_INTERES` si la práctica real muestra que
`"CFO"` encaja mejor.

**Changes pendientes de implementación (en `openspec/changes/`, sin archivar):**

| Change | Estado | Prioridad estimada |
|---|---|---|
| `pricing-quote-engine` | Implementado, bloqueado en push/merge del fundador | — |
| `taty-wompi-link-hitl-gate` | Pendiente — todas las tareas `[ ]` | Alta (bloquea cobros reales vía Wompi) |
| `metrics-dashboard-phase9` | Pendiente — todas las tareas `[ ]` | Media (dashboard de métricas internas) |
| `voicebox-local-voice-adoption` | Pendiente — todas las tareas `[ ]` | Baja (dark launch, requiere consentimiento de Tatiana) |
| `real-data-ingestion-mvp` | Estado ambiguo — `tasks.md` con cambios sin commitear detectados en el working tree al iniciar esta sesión, no investigado por este harness | Revisar |

**Acciones del fundador pendientes (no bloquean, pero deberían resolverse):**
- Verificación E2E con cliente B2B real en `/api/v1/agents/ask` (de `taty-per-tenant-profiles`)
- Activar `HERMES_BRIDGE_TOKEN` en Hermes + Railway (de `hermes-task-queue-tenant-scoping`)
- Merchant-of-record Wompi (task 5.1 de `taty-wompi-link-hitl-gate`, prerequisito para cerrar cobros)
- Stage 11 de `whatsapp-b2b-lead-bridge` (ver arriba)

**Estado:** sin tarea en curso. Próximo paso = el fundador decide si commitea/push
`whatsapp-b2b-lead-bridge` y aplica su migración, o elige otro change.
**Bloqueos:** hay archivos modificados/sin trackear en el working tree que NO pertenecen a este
change (`apps/backend/core/plan_features.py`, `apps/backend/migrations/0046_gmail_sender_map.sql`,
`apps/hermes-hubspot-poller/*`, `openspec/changes/real-data-ingestion-mvp/tasks.md`,
`ai-specs/references/`) — no fueron tocados por esta sesión; parecen de trabajo previo/paralelo sin
commitear. Revisar antes de cualquier commit para no mezclar cambios de distintos changes.
