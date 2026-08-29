# Playbook de ventas — Contexia (para Houston)

Sube este archivo a Houston con la habilidad `set-up-my-sales-info` para que responda con
hechos reales de Contexia en vez de inventar nada.

## Empresa

- **Nombre:** Contexia
- **Qué es:** empresa TIC / AAA (AI Automation Agency) — Entidad B del ecosistema corporativo.
  **No es una firma contable regulada.** Nunca firma estados financieros, declaraciones
  tributarias ni dictámenes.
- **Pitch de 30 segundos:** Contexia es el GPS Financiero de una PyME — le dice cada día cuánta
  plata real tiene, qué debe a la DIAN y hacia dónde va. El producto que hoy está en venta activa
  es el funnel B2C **Renta Natural**: ayuda a personas naturales (dropshippers, creadores,
  freelancers, solopreneurs) a saber si les toca declarar renta y a hacerlo.
- **Etapa:** MVP en producción, captación activa vía WhatsApp (ads de click-to-WhatsApp →
  Taty, el agente conversacional, responde y clasifica).

## Cliente ideal (funnel activo: Renta Natural)

- **Quién:** personas naturales colombianas — dropshippers, creadores de contenido, freelancers,
  solopreneurs — que no saben si superaron los topes de UVT que obligan a declarar renta.
- **Dolor:** incertidumbre fiscal + miedo a una multa de la DIAN por no declarar, o a pagar de más
  por no saber cómo.
- **Trigger:** ingresos/consignaciones/compras/patrimonio del año por encima del umbral de renta
  (varía por categoría — Taty lo detecta en la conversación, no hay una cifra única).
- **Descalificador:** empresas (SAS, régimen común) — el funnel actual es 100% B2C, personas
  naturales. Un lead que resulta ser una empresa no encaja en esta oferta.

## Precio — IMPORTANTE

**El precio NO está confirmado todavía** (decisión pendiente del founder). Nunca cotices ni
insinúes un rango — es exactamente la misma regla que ya sigues por defecto ("no hacer promesas
de precio fuera del playbook"). Si un prospecto pregunta el precio, la respuesta correcta es:
"un asesor de Contexia te confirma el valor exacto para tu caso" — nunca un número.

## Documentos que pide el proceso

1. RUT (foto o PDF)
2. Extractos bancarios del año (PDF o foto)

## CRM conectado

- **Herramienta:** HubSpot (free tier), portal `51867201`.
- **Pipeline:** uno solo, dedicado 100% a este funnel (`default`/Renta Natural). No hay más
  pipelines — el free tier de HubSpot solo permite uno.
- **Etapas** (mapeadas 1:1 desde el sistema fuente de Contexia):

  | Etapa | Significado |
  |---|---|
  | `appointmentscheduled` | Lead nuevo, recién entró por WhatsApp |
  | `qualifiedtobuy` | Mostró interés real de comprar (habló de precio o de declarar) |
  | `presentationscheduled` | Pago iniciado, pendiente de aprobación humana |
  | `decisionmakerboughtin` | Pago aprobado, pasó a manos de la contadora |
  | `closedwon` | Pago confirmado y aprobado |
  | `closedlost` | Pago rechazado |

- **Qué más vas a ver en cada Deal/Contact:** el `amount` es el valor del intento de pago más
  reciente (COP); puede haber una Tarea abierta si el lead está en `presentationscheduled`
  (seguimiento pendiente); puede haber una Nota con el último mensaje que escribió el lead la
  primera vez que entró al sistema.
- **Dueño/routing:** todavía no hay reglas de asignación por dueño — es un solo equipo comercial
  por ahora.
- **Política:** Contexia es la única fuente de verdad de este CRM (sincroniza en un solo sentido
  hacia HubSpot). Igual que tú, Contexia tampoco escribe cambios de vuelta desde HubSpot —así que
  cualquier cosa que anotes o cambies en HubSpot directamente NO vuelve a Contexia. Para que un
  cambio de etapa sea real, tiene que pasar por el flujo de Contexia (pago aprobado, aprobación
  humana, etc.), no por editar el Deal a mano.

## Lo que Houston todavía NO ve

Contexia ya clasifica automáticamente cada conversación de WhatsApp (intención, prioridad,
servicio de interés) pero esa clasificación vive en el sistema de chat (Chatwoot), no en HubSpot
todavía — así que no aparecerá si conectas solo HubSpot. Si más adelante quieres que también
veas esas señales, es un desarrollo aparte; por ahora avísale a tu equipo técnico si lo necesitas.
