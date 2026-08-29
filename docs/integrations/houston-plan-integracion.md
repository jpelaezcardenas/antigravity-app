# Plan: Integración Contexia ↔ Houston (sales agent)

## Context

Houston es una app de escritorio aparte (no vive en `Projects/`, no es código de este repo) con su propio agente "Vendedor" y 18 habilidades de ventas. Se conecta a herramientas externas (CRM, correo, calendario, etc.) vía Composio, configurado desde el panel "Integraciones" de la propia app de Houston — algo que Claude Code no puede hacer por el usuario.

Contexia ya tiene un puente real hacia HubSpot (`hermes-hubspot-poller`, corre local, nunca en Railway/Vercel — soberanía de datos, igual que Hermes/GBrain): sincroniza `crm_leads` → Contacts + Deals en el único pipeline gratis (funnel Renta Natural B2C), con mapeo de etapas, `amount`, Tasks para `POR_APROBAR`, Notes con el último mensaje, e IDs cruzados hacia Chatwoot. Es estrictamente unidireccional (Supabase → HubSpot); nada escribe de vuelta.

Esto encaja exactamente con la propia regla de Houston ("nunca muevo etapas en el CRM sin tu aprobación") y con la razón por la que el founder dijo "por ahora autotag only — usaremos Houston para el pipeline de lead-scoring": Houston puede leer el pipeline real de Contexia vía su conector HubSpot (Composio) sin que Contexia tenga que construir nada nuevo. El trabajo de esta sesión es (1) darle a Houston los hechos reales de Contexia para que no invente nada, y (2) confirmar qué vería exactamente si conecta ese HubSpot.

No hay cambios de código en `antigravity-app` en este plan — es un documento + una verificación.

## Approach

### Parte 1: Playbook para Houston

Genero un archivo Markdown (para subir a Houston vía `set-up-my-sales-info`, que es la modalidad "archivo" — segunda preferencia después de "app conectada") con los campos que Houston necesita y que ya conocemos con certeza del repo:

- **`universal.company`**: Contexia = Entidad B (AAA/TIC, no firma contable regulada — `.antigravity/GROUND_TRUTH.md`). GPS Financiero para PyMEs.
- **`universal.idealCustomer`**: perfil B2C actual = personas naturales que deben declarar renta (dropshippers, creadores, freelancers, solopreneurs) vía el funnel WhatsApp/Renta Natural.
- **`domains.crm`**: HubSpot, portal `51867201`, un solo pipeline (`default`), 4 etapas activas + 2 de cierre — ver tabla en Parte 2.
- **Precio**: explícitamente **NO confirmado** (`precio_confirmado: False` en `taty_lead_router.py::RENTA_OFFER_CONTEXT` — decisión del founder, 2026-08-11, pendiente). Houston debe tratar esto igual que ya trata cualquier precio fuera de playbook: nunca prometerlo.
- **Documentos requeridos**: RUT + extractos bancarios (mismo texto que usa Taty).

Este documento es solo para que Houston no adivine — no le da acceso a nada que no tenga ya.

### Parte 2: Verificación del puente HubSpot

Documento las etapas exactas y qué construye cada Deal/Contact, para que el usuario sepa qué esperar en el panel de Houston al conectar HubSpot (portal `51867201`) vía Composio:

| `crm_leads.stage` | HubSpot `dealstage` |
|---|---|
| `NUEVOS` | `appointmentscheduled` |
| `PROSPECTOS` | `qualifiedtobuy` |
| `POR_APROBAR` | `presentationscheduled` |
| `LISTOS_CONTADORA` | `decisionmakerboughtin` |
| (pago `APPROVED`) | `closedwon` — sobreescribe lo anterior |
| (pago `DECLINED`) | `closedlost` — sobreescribe lo anterior |

Además: `amount` = monto del último intento de pago Wompi (COP); una Task abierta quedó cuando el lead llega a `POR_APROBAR`; una Note con el último mensaje se crea la primera vez que un lead se sincroniza; los Contacts llevan `supabase_customer_id`/`hubspot_contact_id` cruzados también hacia Chatwoot.

**Fuera de alcance / gap a mencionar al usuario:** las 16 etiquetas de Chatwoot (incluida la clasificación de Taty que acabamos de auto-taggear — `intencion`, `prioridad`, `servicio_interes`, etc.) NO llegan a HubSpot hoy. Houston, conectado solo por HubSpot, no las verá. Si el usuario más adelante quiere que Houston también use esas señales, sería un cambio nuevo (Chatwoot no está en la lista de conectores Composio de Houston) — lo dejo anotado, no lo construyo ahora.

**Verificación que el usuario debe hacer en Houston (fuera de mi alcance ejecutar):**
1. En Houston → Integraciones, conectar HubSpot con la cuenta del portal `51867201` (la misma que usa `hermes-hubspot-poller`) — si conecta un portal distinto, Houston vería un CRM vacío o equivocado.
2. Confirmar que Houston lee el pipeline `default` (único pipeline en el free tier).
3. Subir el playbook (Parte 1) vía `set-up-my-sales-info`.

## Files to create

- Un archivo Markdown de playbook (ubicación: carpeta de scratchpad de la sesión, para que el usuario lo descargue y lo suba a Houston — no se commitea al repo, no es código de Contexia).

## Verification

- No hay tests de código (no se toca `antigravity-app`).
- Verificación manual: el usuario confirma en Houston que, tras conectar HubSpot y subir el playbook, `check-my-sales subject=pipeline` o `manage-my-crm action=query` devuelve datos reales del funnel Renta Natural (no inventados) y que Houston respeta el precio no confirmado.
