# Sesión activa

> El líder escribe aquí el plan vivo de la sesión. Los subagentes NO escriben aquí
> su detalle — eso va a `progress/impl_<id>.md` y `progress/review_<id>.md`.
> Al cerrar sesión: mover el resumen a `history.md` y dejar esta plantilla limpia.

**Actualizado:** 2026-08-30

**Change OpenSpec activo:** `taty-wompi-link-hitl-gate` — in_progress

Task in progress: Sections 1-3 — taty-wompi-link-hitl-gate full implementation

Plan:
- Verify implementation in taty_lead_router.py (enqueue helper + sales_interest branch)
- Verify tests in test_taty_lead_router.py (enqueue assertions, no direct link call)
- Verify test_approval_queue_service_wompi_link.py (new file, approve delivers link)
- Verify approve_draft in approval_queue_service.py (wompi_payment_link branch)
- Run pytest -k "taty or approval_queue" and confirm green

**Changes pendientes de implementación (en `openspec/changes/`, sin archivar):**

| Change | Estado | Prioridad estimada |
|---|---|---|
| `taty-wompi-link-hitl-gate` | Pendiente — todas las tareas `[ ]` | Alta (bloquea cobros reales vía Wompi) |
| `metrics-dashboard-phase9` | Pendiente — todas las tareas `[ ]` | Media (dashboard de métricas internas) |

**Último change cerrado:** `taty-whatsapp-renta-sales-capability` — archivado 2026-08-13.
Ver `progress/history.md` para resumen completo.

**Acciones del fundador pendientes (no bloquean, pero deberían resolverse):**
- Verificación E2E con cliente B2B real en `/api/v1/agents/ask` (de `taty-per-tenant-profiles`)
- Activar `HERMES_BRIDGE_TOKEN` en Hermes + Railway (de `hermes-task-queue-tenant-scoping`)
- Merchant-of-record Wompi (task 5.1 de `taty-wompi-link-hitl-gate`, prerequisito para cerrar cobros)

**Estado:** sin tarea en curso. Próximo paso = el fundador elige cuál change implementar.
**Bloqueos:** —
