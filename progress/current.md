# Sesión activa

> El líder escribe aquí el plan vivo de la sesión. Los subagentes NO escriben aquí
> su detalle — eso va a `progress/impl_<id>.md` y `progress/review_<id>.md`.
> Al cerrar sesión: mover el resumen a `history.md` y dejar esta plantilla limpia.

**Change OpenSpec activo:** `reconcile-contexia-app-source-live-pwa`
**Tarea en curso:** — (sin empezar; primera tarea = 1.1 en `tasks.md`)
**Estado:** ready-to-implement (artefactos proposal/design/specs/tasks completos y válidos)
**Plan:**
- MVP Contexia Cliente Cero — primer incremento: reconciliar `contexia-app/` source para que un `npm run build` reproduzca la UI real del cliente CON la Caja Real en vivo horneada, retirando el `<script>` a mano de `app/overview.html`.
- Fuente autoritativa de tareas: `openspec/changes/reconcile-contexia-app-source-live-pwa/tasks.md` (7 grupos, incluye Stage 11).
- Contexto crítico: la UI real solo existe hoy como export en `app/`; `contexia-app/` renderiza placeholders (CLAUDE.md §9 EXCEPCIÓN). NO regenerar `app/` a ciegas hasta lograr paridad verificada.

**Bloqueos:** —
