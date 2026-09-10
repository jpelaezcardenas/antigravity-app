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

**Actualizado:** 2026-09-09 (sesión 2)

**Trabajo de esta sesión (leader -> implementer -> reviewer, sin push):**
`taty-voice-outbound-calls`, Tareas 2-6 implementadas y APROBADAS por el reviewer. Tarea 1
(cadence) ya estaba hecha y desplegada; Tareas 7-9 (llamadas reales, fases de rollout) NO se
tocaron -- requieren checkpoints explícitos del fundador que no se han dado. Detalle completo:
`progress/impl_taty_voice_outbound_2_3_4.md` + `progress/review_taty_voice_outbound_2_3_4.md`.

Resumen verificado:
- Endpoint nuevo `POST /internal/voice/outbound-call` (`presentation/voice_outbound_endpoints.py`),
  mismo patrón `INTERNAL_API_KEY` fail-closed que los pollers existentes. Solo acepta
  `{lead_id, tenant_id}`; el teléfono siempre se resuelve server-side desde `crm_leads`; un
  `phone` en el body se ignora (pydantic `extra=ignore`).
- Un lead `crm_leads.lead_type = "business_interest"` (B2B) es rechazado ANTES de cualquier
  lógica de Twilio/teléfono -- verificado leyendo el orden de ejecución, no solo confiando en tests.
- **La voz clonada de Tatiana NUNCA se usa en este código, bajo ningún estado de flag.** La
  apertura siempre se sintetiza con la voz genérica propia de Twilio (`<Say voice="Polly.Lupe"
  language="es-MX">`, `_build_twiml` en el nuevo endpoint). `VOICE_OUTBOUND_CALLS_ENABLED` se
  agregó como flag NUEVO e independiente de `VOICE_ENABLED` (WhatsApp), default `false`, y no
  existe ningún código que seleccione la voz clonada aunque el flag esté en `true` (solo loguea un
  warning y sigue con la voz genérica). Confirmado por el reviewer con grep dedicado + lectura
  completa de las 3 funciones relevantes.
- `services/twilio_client.py` es un wrapper `httpx` plano (no se agregó el SDK `twilio` a
  requirements.txt); las credenciales Twilio viven solo en `config.py`/Railway; confirmado
  `grep -ri twilio apps/chatwoot-bridge` sin resultados.
- Gap documentado, no resuelto en esta sesión: la síntesis real vía VoiceBox local para este flujo
  específico requiere resolver la misma imposibilidad de red que ya se resolvió para las notas de
  voz de WhatsApp (Railway no puede alcanzar VoiceBox local) -- queda como follow-up explícito, no
  se construyó un túnel ni se expuso VoiceBox a internet.
- Tarea 3 (STT): `apps/chatwoot-bridge/whisper_client.py` es el primer llamador real del
  placeholder `LOCAL_WHISPER_URL` (antes sin usar). No apunta a un Whisper real corriendo --
  acción externa del fundador/infra.
- Tarea 4.1 (requisito legal colombiano de revelación de IA): **no se pudo verificar con
  certeza** -- esta sesión no tiene acceso a bases de datos legales. Se documentó la duda
  explícitamente y se usó el default seguro (revelar siempre la identidad de IA antes de
  cualquier pregunta), tal como pide `design.md`. No se inventó ninguna cita legal.
- Acción externa del fundador pendiente, no bloqueante para el resto: cuenta Twilio real +
  número colombiano (Tarea 2.3); instancia real de Whisper corriendo (Tarea 3.2 parcial);
  consentimiento escrito/fechado/revocable de Tatiana antes de poder encender
  `VOICE_OUTBOUND_CALLS_ENABLED` alguna vez (sigue en `false`).
- 37 tests nuevos en verde; barrido de regresión completo re-ejecutado independientemente por el
  reviewer, listas de fallos preexistentes idénticas contra el árbol sin modificar (cero
  regresiones nuevas).
- `feature_list.json` actualizado con esta entrada como `pending` (no archivado -- faltan las
  Tareas 7-9, gateadas por el fundador). **No se hizo commit ni push** -- el diff queda en el
  working tree para que el fundador decida cuándo confirmar.

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
