# Mapa del proceso Hermes–Claude Code existente

Estado: **POR COMPLETAR CON EL SISTEMA REAL**. Este archivo evita que el playbook invente la infraestructura comercial.

## 1. Entradas

| Entrada | Canal/sistema real | Evento disparador | Datos permitidos | Consentimiento requerido | Propietario |
|---|---|---|---|---|---|
| Formulario de Renta | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] |
| WhatsApp entrante | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] |
| Referido | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] |
| Lead B2B | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] |

## 2. Fuente canónica y estados

- Sistema maestro de leads/oportunidades: `[POR CONFIRMAR]`
- Identificador estable de persona: `[POR CONFIRMAR]`
- Identificador estable de empresa: `[POR CONFIRMAR]`
- Relación persona–empresa: `[POR CONFIRMAR]`
- Deduplicación: `[POR CONFIRMAR]`
- Estados actuales del pipeline: `[PEGAR LISTA EXACTA]`
- Razones de pérdida/no-fit: `[PEGAR LISTA EXACTA]`

## 3. Hermes

| Flujo/agente | Entrada exacta | Salida exacta | Puede escribir | Requiere aprobación | Fallback humano |
|---|---|---|---|---|---|
| Triage de renta | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] |
| Calificación B2B | [POR CONFIRMAR] | [POR CONFIRMAR] | [POR CONFIRMAR] | Sí | [POR CONFIRMAR] |
| Generación de mensaje | [POR CONFIRMAR] | Borrador | No | Sí | [POR CONFIRMAR] |
| Cotización | [POR CONFIRMAR] | Recomendación/banda | No precio final | Sí, Tatiana | Tatiana |

## 4. Claude Code

- Repositorio(s) y rama(s) autorizadas: `[POR CONFIRMAR]`
- Fuente de ground truth: `[POR CONFIRMAR]`
- Skills/comandos ya existentes: `[POR CONFIRMAR]`
- Hooks/gates ya existentes: `[POR CONFIRMAR]`
- Formato de artefactos: `[POR CONFIRMAR]`
- Ruta de reportes/telemetría: `[POR CONFIRMAR]`

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

- Reintentos permitidos: `[POR CONFIRMAR]`
- Cola de excepción: `[POR CONFIRMAR]`
- Pausa de automatización: `[POR CONFIRMAR]`
- Registro de consentimiento: `[POR CONFIRMAR]`
- Audit log: `[POR CONFIRMAR]`
- Retención/borrado: `[POR CONFIRMAR]`
- Procedimiento de incidente: `[POR CONFIRMAR]`
- Idempotencia por aprobación/campaña/tarea: `[POR CONFIRMAR]`
- Reconciliación de publicación y gasto: `[POR CONFIRMAR]`
- Registro de créditos Manus estimados/reales: `[POR CONFIRMAR]`

## Gate de integración

No conectar una habilidad de este kit a un sistema de escritura o envío hasta que todas las celdas críticas estén completas, probadas con datos sintéticos y aprobadas por los propietarios. Los 300 créditos diarios de Manus son capacidad disponible, no una cuota que deba agotarse.
