# Métrica de éxito del plan maestro — DECIDIDA 2026-09-09

**Estado: decidido por el fundador.** Opción elegida: **Opción 1 — declaraciones de renta persona
natural vendidas esta temporada**, vía `crm_wompi_transactions.status = 'APPROVED'` cruzado con
`crm_leads`. Nace del hueco #5 identificado en el plan maestro
(`estaba-cometiendo-un-error-scalable-goose.md`, sección "ESTADO VIVO DEL PLAN"): cada frente tenía
verificación técnica end-to-end, pero no existía un número de negocio que dijera "el loop está
cerrado". Las Opciones 2 y 3 (abajo) quedan como métricas de diagnóstico por frente, no como el
número oficial.

**Riesgo real, sin resolver todavía:** esta métrica depende de que `taty-wompi-link-hitl-gate`
(hoy con todas sus tareas `[ ]`) esté completo — hoy los pagos de Wompi no fluyen de punta a punta
sin ese change, así que el número puede quedarse en 0 aunque haya ventas reales cerradas por otra
vía manual. El fundador no confirmó todavía si quiere esperar a que ese gate cierre antes de que el
número sea representativo — queda como pregunta abierta, no asumida.

## Por qué esto es una decisión de negocio, no de ingeniería

Ninguna de las tres opciones de abajo requiere código nuevo — las tres se pueden consultar hoy
contra datos que ya existen. Lo que falta es que el fundador elija **cuál** importa y **qué
umbral** cuenta como éxito (ej. "20 declaraciones vendidas" vs. "50"). Ese número no se puede
inventar aquí.

## Opción 1 — Declaraciones de renta persona natural vendidas esta temporada

- **Qué mide:** conversión real del embudo B2C (`taty-whatsapp-renta-sales-capability`,
  `pricing-quote-engine`) en ventas cerradas, no solo leads.
- **Fuente de datos real:** `crm_wompi_transactions.status = 'APPROVED'` cruzado con
  `crm_leads` (mismo `lead_id`), filtrado a la ventana de temporada DIAN (ago-oct 2026). Es el
  mismo dato que ya alimenta el pipeline de HubSpot (`closedwon`, Decisión #20).
- **Ventaja:** es la métrica más directamente ligada a ingreso real, no a actividad.
- **Riesgo:** depende de que el HITL gate de Wompi (`taty-wompi-link-hitl-gate`, aún `pending`)
  esté cerrado — hoy los pagos no fluyen de punta a punta sin ese change.

## Opción 2 — Leads B2B capturados por WhatsApp desde que se activó el Frente A

- **Qué mide:** si el puente `whatsapp-b2b-lead-bridge` (ya archivado, cerrado 2026-09-09) está
  generando volumen real, no solo la corrección estructural.
- **Fuente de datos real:** `SELECT count(*) FROM crm_leads WHERE lead_type = 'business_interest'
  AND created_at >= '2026-09-09'` — consulta directa, sin dashboard nuevo, disponible hoy mismo.
- **Ventaja:** aísla el efecto de un solo change ya cerrado, útil para confirmar que el arreglo
  estructural realmente mueve una aguja de negocio, no solo de ingeniería.
- **Riesgo:** un lead capturado no es un cliente — mide llegada al embudo, no cierre.

## Opción 3 — Tasa de conversión punta a punta del embudo social (si `b2c-social-lead-capture` llega a producción)

- **Qué mide:** de los leads capturados por la campaña de redes sociales
  (`crm_leads.source LIKE 'facebook%' OR 'instagram%' OR 'tiktok%'`), cuántos llegan a
  `stage = 'LISTOS_CONTADORA'` y cuántos de esos pagan (Opción 1).
- **Fuente de datos real:** el campo `source` que este mismo change (`b2c-social-lead-capture`)
  está añadiendo a `crm_leads` (migración pendiente de aplicar, ver `tasks.md` Tarea 1).
- **Ventaja:** mide el efecto específico de la inversión en pauta, no solo el canal orgánico de
  WhatsApp que ya existía.
- **Riesgo:** solo es medible una vez la campaña esté realmente corriendo con tráfico pagado —
  hoy no hay pauta activa, así que el número sería 0 por semanas si se adopta antes de tiempo.

## Recomendación (no vinculante, para facilitar la decisión, no para tomarla)

Si el fundador quiere UN solo número para el plan completo, la Opción 1 (declaraciones vendidas)
es la más cercana a "esto cerró el loop de negocio", porque integra tanto B2C como la razón de ser
de la temporada. Las Opciones 2 y 3 son buenas métricas de **diagnóstico por frente**, no
sustitutos de un número único.

## Qué falta para cerrar esto

- [ ] El fundador elige una opción (o combina varias) y define el umbral de éxito.
- [ ] Si elige la Opción 1, confirmar que quiere esperar a que `taty-wompi-link-hitl-gate` esté
      completo antes de que el número sea significativo.
- [ ] Si elige la Opción 3, confirmar que no se mide hasta que exista pauta paga real corriendo.

Una vez decidido, esto se documenta en el propio plan maestro
(`estaba-cometiendo-un-error-scalable-goose.md`) como la métrica oficial, reemplazando el hueco #5.
