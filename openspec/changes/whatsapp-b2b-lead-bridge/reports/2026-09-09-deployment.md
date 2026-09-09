# Deployment report — whatsapp-b2b-lead-bridge

**Fecha:** 2026-09-09
**Commit de código:** `75ae6e0` (feature) → mergeado con `origin/main` en `73f781e` →
pusheado a `main`.
**Deploy branch:** `main`.

## Stage 11 — checklist

- [x] **11.1 Migración `0049_crm_leads_lead_type.sql` aplicada en Supabase**
  (proyecto `kpynymwghfwshvcvevxq`, con confirmación explícita del fundador). Verificado en
  vivo contra `information_schema.columns`: `lead_type text`, `is_nullable=YES`,
  `column_default=NULL`. De los 5 `crm_leads` existentes, 0 tienen `lead_type` seteado — sin
  backfill, tal como diseñado.
- [x] **11.2 `git commit` + `push` a `main`.** La rama de feature (`feat/voicebox-local-voice-adoption`)
  estaba 12 commits detrás de `origin/main` (trabajo de `pricing-quote-engine` /
  `pricing-catalog-and-operator-quote` / `taty-pricing-skill`, ya archivado y desplegado en una
  sesión previa) — se hizo `git merge origin/main` antes de push. Dos conflictos reales:
  - `ARCHITECTURE.md`: colisión de numeración — ambas ramas usaban "Decisión #24" para cosas
    distintas (VoiceBox vs. catálogo de precios). Resuelto renumerando la entrada de VoiceBox a
    **Decisión #26** (después de la #25 ya existente en `main`), sin perder contenido de
    ninguna de las dos.
  - `progress/current.md`: archivo de tracking del harness con estado desactualizado de ambos
    lados (el bloqueo de `pricing-quote-engine` ya estaba resuelto en `main`). Reescrito para
    reflejar el estado real post-merge.
  - `crm_service.py` y `taty_lead_router.py` (los archivos de código con overlap real) se
    auto-mergearon limpio, sin conflicto de contenido.
  - Push: `d9602b2..73f781e  feat/voicebox-local-voice-adoption -> main`.
- [x] **11.3 Railway deploy activo.** Deployment `79eb9162-868c-4ea8-a0eb-1cf8d3e0c4a8`,
  disparado por el push, terminó en `SUCCESS`. `GET /api/v1/health` responde `200` en
  `antigravity-app-production-175a.up.railway.app`.
- [~] **11.4 Verificación E2E.** **No se pudo hacer con un mensaje real de WhatsApp** — Chatwoot
  corre local en el equipo del fundador (Decisión #19), fuera de este alcance y sin manejo de
  credenciales. En su lugar se ejecutó el código exacto ya desplegado en `main`:
  - `classify_lead_intent()` clasifica correctamente 4 casos reales, incluyendo la precedencia
    diseñada (`payment_confirmation` gana sobre `business_interest` cuando el mensaje menciona
    ambos):
    - `"Somos una SAS y necesitamos ayuda con la contabilidad del negocio"` → `business_interest`
    - `"Ya pagué, aquí está el comprobante"` → `payment_confirmation`
    - `"Estoy interesado en el servicio de declaración de renta"` → `sales_interest`
    - `"Hola, buenos días"` → `unknown`
  - `_INTENT_TO_SERVICIO_INTERES` en el bridge desplegado confirma el mapeo:
    `{"sales_interest": "renta", "business_interest": "creacion_empresa"}`.
  - `route_lead_message()` llama a `CrmService.advance_lead(lead_id, current_stage,
    lead_type="business_interest")` cuando el intent es `business_interest` — confirmado leyendo
    el código real en `taty_lead_router.py:382-388` y `crm_service.py:548-563`.
  - **Pendiente del fundador, no bloqueante:** enviar un mensaje real por WhatsApp con lenguaje
    de negocio, seguido de un mensaje normal de Renta Natural, y confirmar en `crm_leads` que
    solo el primero tiene `lead_type` seteado y que el segundo no cambió su comportamiento
    habitual. Esto requiere además **reiniciar el servicio local del Chatwoot bridge**
    (`ContexiaChatwootBridge`, tarea programada de Windows) para que recoja el `main.py`
    actualizado — no se reinicia solo, corre local y no pasa por Railway/Vercel.
- [x] **11.5 Este reporte.**

## Suites verificadas antes del push

- Backend completo (excluyendo 3 archivos con error de colección preexistente, documentado en
  memoria del proyecto): **1172 passed, 33 failed, 120 skipped** — los 33 fallos son el baseline
  preexistente (shadow_gl stages, wizard, radar tenant scoping, secure_llm); **ninguno** en
  `test_taty_lead_router.py` ni `test_crm_service.py`. Confirmado también reproduciendo los mismos
  33 fallos contra un worktree limpio de `origin/main` antes del merge.
- `apps/chatwoot-bridge`: **85 passed, 2 failed** — ambos fallos confirmados preexistentes en
  `origin/main` (worktree de verificación aparte), no relacionados con este change:
  `test_posts_an_incoming_message` y `test_reply_comes_from_the_sales_router_not_hermes`.

## Resumen de non-goals verificados (Grupo 5 del `tasks.md`, ya confirmado por el `leader`)

Ningún path de este change crea filas en `tenants`/`b2b_clients`, y `hermes-hubspot-poller` no
fue tocado — un `crm_leads.lead_type` seteado solo hace visible el lead para un operador humano
vía el flujo manual de alta ya existente (`crm-alta-tiered-provisioning`).

## Decisión de diseño abierta, no bloqueante

El mapeo `business_interest → servicio_interes="creacion_empresa"` (en vez de `"CFO"`, ambos
valores reales confirmados en Chatwoot) es un cambio de una línea en
`apps/chatwoot-bridge/main.py::_INTENT_TO_SERVICIO_INTERES` si la práctica real muestra que
`"CFO"` describe mejor el intent.
