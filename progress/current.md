# Sesión activa

> El líder escribe aquí el plan vivo de la sesión. Los subagentes NO escriben aquí
> su detalle — eso va a `progress/impl_<id>.md` y `progress/review_<id>.md`.
> Al cerrar sesión: mover el resumen a `history.md` y dejar esta plantilla limpia.

**Actualizado:** 2026-09-08

**Change OpenSpec activo:** `pricing-quote-engine` — implementado, commit en rama
`feat/pricing-quote-engine`. NO pusheado, NO desplegado, migración 0048 NO aplicada.

Qué quedó:
- `uvt_values` (UVT por año gravable, pesos completos, sembrada 2025/2026 con sus resoluciones)
  + `services/uvt_service.py`. Cero constantes de UVT en código — un test lo verifica leyendo
  el propio source del módulo.
- `b2b_clients.service_band` (`micro|estandar|complejo`). **Hallazgo:** `monthly_fee_cents` YA
  existía desde la migración 0020 (verificado en vivo contra Supabase) — el handoff decía que no.
  Lo que faltaba era la banda. De paso, el honorario ahora es editable después del alta.
- `GET /api/v1/pricing/pre-cotizacion` — tenant del JWT vía `resolve_request_tenant_scope()`,
  404 si no resuelve, solo lectura, sin gating por plan. `core/plan_features.py` intacto.
- 77 tests nuevos, todos verdes. `tsc --noEmit` limpio.

**Bloqueado en el fundador, EN ESTE ORDEN:**
1. Aplicar migración 0048 **antes** de desplegar (`list_b2b_clients` ya proyecta `service_band`
   y su `except` cae a datos demo — desplegar primero mostraría clientes falsos en el Búnker).
2. Push de `feat/pricing-quote-engine` (main auto-despliega).

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
