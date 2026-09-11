# Mapa del proceso Hermes–Claude Code existente

Estado: **Completado 2026-09-11 con el sistema real**, verificado en código/producción esta sesión
y en sesiones previas (no inventado). Las celdas que siguen `[POR CONFIRMAR]` son genuinamente
desconocidas — no se rellenaron con una suposición. Corrección importante frente a la plantilla
original: **Hermes no hace triage ni cotización por lead** — esa lógica vive en el backend
(Taty/`TatyAgentService`, Railway). Hermes es el orquestador local de tareas programadas
(Scheduled Jobs) y agentes de escritorio; el §3 de abajo se corrigió para reflejar eso, no lo que
la plantilla original asumía.

## 1. Entradas

| Entrada | Canal/sistema real | Evento disparador | Datos permitidos | Consentimiento requerido | Propietario |
|---|---|---|---|---|---|
| Formulario de Renta | Landing `contexia.online/renta-natural` → `POST /api/v1/crm/social-capture/partial` (change `b2c-social-lead-capture`, en producción) | Número de WhatsApp válido (captura parcial) o envío del formulario (captura completa) | Nombre, teléfono, respuestas del formulario | Sí, checkbox en el formulario | Backend / Entidad B (captación); handoff a Entidad A en el triage |
| WhatsApp entrante | Meta Cloud API → webhook consolidado (`taty-channel-consolidation`) → tabla `whatsapp_inbound_events` (durable, `whatsapp-durable-inbox`) → poller de `apps/chatwoot-bridge` → Chatwoot inbox `1` + `TatyAgentService` | Mensaje real de WhatsApp, firma HMAC verificada | Contenido del mensaje, número de teléfono | Implícito en iniciar la conversación; explícito en el guion de Taty (`GUIONES.md` §2.7) antes de pedir documentos | Backend (canal) / Tatiana (servicio) |
| Referido | **No implementado como flujo propio todavía** — `crm_leads.source` (migración `0052`) admite un valor de origen genérico, pero no existe tracking de "quién refirió a quién" | N/A | N/A | N/A | Ver `3.6-bucle-viral.md` — hipótesis, no construido |
| Lead B2B | Mensaje de WhatsApp clasificado como `business_interest` por `classify_lead_intent()` (`taty_lead_router.py`, change `whatsapp-b2b-lead-bridge`, en producción) → `CrmService.whatsapp_intake()`/`advance_lead()` | Palabras clave de intención de negocio detectadas por Taty | Mismo mensaje de WhatsApp, sin dato adicional | Igual que WhatsApp entrante | Backend |

## 2. Fuente canónica y estados

- Sistema maestro de leads/oportunidades: **`crm_leads`** (Supabase) para el funnel B2C Renta
  Natural; **`b2b_clients`**/`tenants` para clientes B2B — son dos tablas separadas, no un CRM
  unificado (HubSpot sincroniza desde ambas, unidireccional, solo lectura desde el Búnker).
- Identificador estable de persona: número de teléfono normalizado (`crm-lead-phone-dedup`,
  capability real en `openspec/specs/`).
- Identificador estable de empresa: `tenants.id` (UUID) / `b2b_clients.id`.
- Relación persona–empresa: `crm_leads.lead_type` distingue `business_interest` (B2B) del resto
  (B2C); un lead B2B calificado se convierte en `b2b_clients` + `tenants` en el alta manual del
  Búnker, no automáticamente.
- Deduplicación: por teléfono normalizado, capability `crm-lead-phone-dedup`.
- Estados actuales del pipeline (B2C, verificado en `ARCHITECTURE.md` Decisión #20): `NUEVOS` →
  `PROSPECTOS` → `POR_APROBAR` → `LISTOS_CONTADORA`, con `crm_wompi_transactions.status`
  `APPROVED`/`DECLINED` sobreescribiendo a `closedwon`/`closedlost` en HubSpot.
- Razones de pérdida/no-fit: `[POR CONFIRMAR]` — no existe un campo estructurado para esto hoy;
  se infiere solo de que el lead deja de responder.

## 3. Hermes — corregido: no hace triage por lead, orquesta tareas programadas

| Job/perfil real | Qué hace | Frecuencia | Puede escribir | Requiere aprobación | Fallback humano |
|---|---|---|---|---|---|
| Pulso Diario | Agrega estado operativo diario y lo empuja al backend (`POST /agents/pulso-diario/insights`) | Programado (Scheduled Job) | Sí, vía endpoint gateado por `HERMES_BRIDGE_TOKEN` | No (push de datos, no acción comercial) | N/A |
| Conciliación Shadow GL | Reconcilia el libro derivado contra las fuentes ingeridas | Programado | Sí, dentro de su propio dominio | No | N/A |
| Radar Predictivo | Alimenta la proyección de caja a 13 semanas | Programado | Sí, dentro de su dominio | No | N/A |
| Centinela Fiscal | Genera alertas fiscales | Programado | Sí (tabla de alertas) | No | N/A |
| Auditoría Sombra | Auditoría técnica/consistencia | Programado | Sí, dentro de su dominio | No | N/A |
| Social Ops | Pipeline, inbox, ideas, métricas | Programado | Sí, borradores | Sí, HITL en Búnker | Humano vía Búnker |
| Metrics Snapshot | Snapshot de métricas del negocio | Programado | Sí (tabla `metrics_snapshots`) | No | N/A |

**Lo que Hermes NO hace**: triage de renta, calificación B2B, generación de mensaje a un lead
individual, ni cotización — todo eso ocurre en el backend (Taty/`TatyAgentService`, corriendo en
Railway, usando la cascada de LLM de Decisión #7), disparado por el mensaje del propio lead, no
por un Scheduled Job de Hermes.

## 4. Claude Code

- Repositorio(s) y rama(s) autorizadas: `antigravity-app`, rama `main` (auto-deploy a Vercel/Railway
  en cada push — ver CLAUDE.md §8).
- Fuente de ground truth: `.antigravity/GROUND_TRUTH.md` (identidad/legal, manda sobre todo) →
  `ARCHITECTURE.md` (arquitectura) → `HARNESS.md` (cómo trabajan los agentes) → `openspec/changes/`
  (qué se construye ahora).
- Skills/comandos ya existentes: `ai-specs/skills/` — incluye ahora las 18 skills del kit GTM
  (`contexia-readiness`, `contexia-renta-campaign`, etc.) además de las skills técnicas previas
  (`openspec-propose`, `adversarial-review`, etc.).
- Hooks/gates ya existentes: `init.sh` (gate verde del harness), Stage 11 obligatorio antes de
  archivar cualquier change (CLAUDE.md §8).
- Formato de artefactos: changes de OpenSpec (`proposal.md`/`design.md`/`specs/`/`tasks.md`) por
  cada iniciativa, con reporte de deployment en `reports/`.
- Ruta de reportes/telemetría: `openspec/changes/<id>/reports/YYYY-MM-DD-deployment.md`.

## 5. Manus Pro

El paquete v1.1.0 del 25 de julio de 2026 documenta tres proyectos ya creados: **CTX — Strategy & Market Intelligence**, **CTX — Content Studio** y **CTX — Social Operations**. Su configuración actual en la cuenta debe verificarse; los archivos locales no prueban que conectores, tareas, webhooks o permisos sigan activos.

| Proyecto | Entrada permitida | Salida | Puede actuar | Requiere aprobación | Datos prohibidos |
|---|---|---|---|---|---|
| Strategy | pregunta de investigación + fuentes permitidas | evidence/decision brief | solo consulta pública | para cualquier acción externa | finanzas, expediente tributario, CRM completo |
| Content | brief versionado + claims aprobables | Campaign Package `DRAFT` | crear borradores/activos | antes de uso/publicación | secretos y datos personales innecesarios |
| Operations | paquete exacto aprobado + hash + alcance | evidencia y telemetría | Facebook/Instagram/Meta dentro del alcance | Búnker/humano; granular para pauta | finanzas, credenciales, cambios no aprobados |

- IDs actuales de los tres proyectos: `[POR CONFIRMAR EN MANUS]`
- Conectores instalados y scopes: `[POR CONFIRMAR EN MANUS]`
- Cuenta/página Meta allowlisted: `[POR CONFIRMAR]`
- Perfil dedicado de navegador: `[POR CONFIRMAR]`
- Límite diario de créditos por tarea: `[POR DEFINIR TRAS MEDIR COSTO REAL]`
- Propietario del presupuesto de pauta: `[POR CONFIRMAR]`
- Kill switch y fallback humano: `[POR CONFIRMAR]`
- Endpoint, firma y reconciliación del webhook: `[POR CONFIRMAR EN CÓDIGO Y PRODUCCIÓN]`
- Telegram: `[POR CONFIRMAR; canal de informes, no autoridad de aprobación]`

Contrato completo: `reference/MANUS-EXECUTION-CONTRACT.md`.

## 6. Handoffs y responsabilidades

| Transición | Criterio observable | De | A | Datos compartidos | Autorización | SLA real |
|---|---|---|---|---|---|---|
| Lead → triage | [POR CONFIRMAR] | Marketing | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] |
| Triage → Entidad A | [POR CONFIRMAR] | [POR CONFIRMAR] | Tatiana/Entidad A | Mínimo necesario | [POR CONFIRMAR] | [POR CONFIRMAR] |
| Servicio A → oferta B | Valor entregado + consentimiento comercial separado | Entidad A | Contexia B | Solo autorizado | Sí | [POR CONFIRMAR] |
| Venta B → onboarding | Contrato/pago/gate de capacidad | Ventas | Producto/CS | [POR CONFIRMAR] | N/A | [POR CONFIRMAR] |
| Brief → borrador | estrategia y claims versionados | Claude Code/Hermes | Manus Content | mínimo necesario | revisión humana | [POR CONFIRMAR] |
| Aprobación → ejecución | `approval_id` válido + hash + cuenta + scope | Búnker/Hermes | Manus Operations | paquete aprobado | sí; nueva versión si cambia algo | [POR CONFIRMAR] |
| Ejecución → aprendizaje | evidencia reconciliada | Manus/backend | Hermes/Búnker/Claude Code | métricas mínimas | N/A | [POR CONFIRMAR] |

## 7. Aprobaciones

- Precio final: **Tatiana** según el anexo vigente.
- Firma/presentación profesional: **Entidad A/profesional habilitado**.
- Publicación, pauta y envío: humano/Búnker `[PROPIETARIO Y REGLA POR CONFIRMAR]`; Manus nunca aprueba.
- Uso de testimonio/caso: `[POR CONFIRMAR]`.
- Cambio de claim: `[POR CONFIRMAR]`.
- Acceso o transferencia de datos: `[POR CONFIRMAR]`.

## 8. Fallos y auditoría

- Reintentos permitidos: Meta reintenta el webhook si no recibe 200 (comportamiento de la propia
  plataforma); el poller de `whatsapp-durable-inbox` deja un evento sin confirmar (`ack`) si su
  procesamiento falla, para que se reintente en el siguiente ciclo — verificado en el código
  (`inbox_poller.py`) esta sesión.
- Cola de excepción: `whatsapp_inbound_events` con `processed_at IS NULL` es, de facto, la cola de
  pendientes/excepción — verificado en vivo (0 atascados al momento de esta sesión).
- Pausa de automatización: etiqueta `bot_off` en la conversación de Chatwoot pausa la respuesta
  automática de Taty (verificado en el código del poller).
- Registro de consentimiento: `[POR CONFIRMAR]` — no se encontró una tabla dedicada de
  consentimiento; el checkbox del formulario de captación no persiste su texto exacto.
- Audit log: `agent_operations` (Supabase) para invocaciones de agentes; no existe un audit log
  unificado para el embudo comercial completo.
- Retención/borrado: `[POR CONFIRMAR]` — no verificado esta sesión.
- Procedimiento de incidente: informal — ver el patrón ya usado dos veces para el traffic-cutover
  de Railway (`railway_redeploy` manual), documentado en los reportes de Stage 11.
- Idempotencia por aprobación/campaña/tarea: para WhatsApp, `meta_message_id UNIQUE` en
  `whatsapp_inbound_events` la garantiza a nivel de base de datos (verificado esta sesión: 3 envíos
  duplicados del mismo evento producen una sola fila). Para Manus, `[POR CONFIRMAR EN MANUS]`.
- Reconciliación de publicación y gasto: `[POR CONFIRMAR]` — depende del circuito Manus, no
  verificado esta sesión.
- Registro de créditos Manus estimados/reales: `[POR CONFIRMAR EN MANUS]`.

## Gate de integración

No conectar una habilidad de este kit a un sistema de escritura o envío hasta que todas las celdas críticas estén completas, probadas con datos sintéticos y aprobadas por los propietarios. Los 300 créditos diarios de Manus son capacidad disponible, no una cuota que deba agotarse.
