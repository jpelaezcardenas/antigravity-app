# Design: hermes-jarvis-contexia

**Change:** hermes-jarvis-contexia  
**Fecha:** 2026-09-01  
**Estado:** design (detalla implementación de cada fase)

---

## Decisiones de arquitectura

### D1: Brief matutino = dos llamadas HTTP en paralelo

**Decisión:** Hermes hace dos llamadas **no bloqueantes** (paralelo/async):
1. `POST /api/v1/jarvis/brief` (Railway) → contexto financiero
2. `GET /sell-machine/tasks/recent?hours=24` (Manus local) → contexto comercial

**Por qué:** evita la latencia de esperar a una si la otra es lenta; fail-graceful si una falla.

**Implementación:** Hermes bash script usa `curl` con timeout y captura errores; cada falla logea pero no bloquea.

---

### D2: Hermes accede a Manus localmente, no via Railway

**Decisión:** La URL de Manus (`http://localhost:MANUS_PORT/api/...`) vive en `~/.hermes/config.yaml`, no en env vars de Railway.

**Por qué:** soberanía de datos; las credenciales de Manus nunca tocan Railway.

---

### D3: Brief es sync y encolable

**Decisión:** El cron ejecuta el script de forma **síncrona** (espera respuesta de ambas fuentes antes de redactar).
Si alguna tarda >5s, timeout y omite esa sección.

**Por qué:** el fundador quiere un brief completo cada mañana, no parcial.

---

### D4: Telegram webhook + gateway dinámico

**Decisión:** el webhook vive en Railway (`POST /api/v1/channels/jarvis/webhook`), pero resuelve dinámicamente
la URL de Hermes desde `hermes_tunnel[id='current']` en Supabase (reutiliza el patrón de `/api/hermes/status.ts`).

---

## Fase A — Jarvis Personal por Telegram

### A1: Backend `jarvis_endpoints.py`

Estructura:
- `handle_webhook()` — valida token Telegram, reenvía a Hermes
- `brief_endpoint()` — agrega contexto financiero para cron matutino
- `chat_proxy()` — proxy de chat desde Búnker a Hermes
- `status_proxy()` — health check del gateway (admin only)

Patrones:
- Reutilizar `resolve_hermes_gateway_url()` (como en `/api/hermes/status.ts`)
- Validación de token Telegram (HMAC-SHA256)
- Timeouts a Hermes: >5s → 504
- Error handling: log y devolver graceful

### A2: Config en `apps/backend/config.py`

Agregar:
```
TELEGRAM_BOT_TOKEN_JARVIS
TELEGRAM_WEBHOOK_SECRET_JARVIS
TELEGRAM_JUAN_DAVID_CHAT_ID
JARVIS_ENABLED = bool(TELEGRAM_BOT_TOKEN_JARVIS)
```

### A3: Router en `apps/backend/presentation/router.py`

Registrar JarvisEndpoints router bajo `/jarvis`.

### A4: Hermes skill `jarvis-personal.md`

Define identidad, contexto, herramientas del asistente personal.

### A5: Cron `jarvis-morning-brief.sh`

Bash script que:
- Llama Railway (`POST /api/v1/jarvis/brief`) → financiero
- Llama Manus (`GET /sell-machine/tasks/recent?hours=24`) → comercial
- Agrega contexto + redacta brief via Hermes skill
- Envía a Telegram

Timeout: 5s por llamada, fail-graceful omite sección.

Registrar en `jobs.json` con schedule `0 9 * * *` (9 AM COT diario).

---

## Fase B — Búnker Agentic OS

### B1: Components en `contexia-app/components/bunker/agentic-os/`

- `AgenticOsSection.tsx` — sección principal, feature-gated por tier
- `HermesStatusCard.tsx` — health del gateway + agentes activos
- `JarvisChatInterface.tsx` — chat bidireccional (POST /api/v1/jarvis/chat)
- `CronJobsMonitor.tsx` — lista de cron jobs + último estado
- `VoiceToggle.tsx` — Web Speech API (solo enterprise)

### B2: Client `jarvis-client.ts`

Métodos:
- `chat(message, tenantId)` → POST /api/v1/jarvis/chat
- `status()` → GET /api/v1/jarvis/status

### B3: Config endpoints en `contexia-app/lib/config.ts`

```
JARVIS_CHAT_URL: "/api/v1/jarvis/chat"
JARVIS_STATUS_URL: "/api/v1/jarvis/status"
```

### B4: Update `contexia-app/app/app/bunker/page.tsx`

Quitar "agentic-os" de `PLACEHOLDER_SECTIONS`.

---

## Fase C — Tier display y feature gating

### C1: Feature flags en `plan_features.py`

```python
"growth": {..., "jarvis_chat"}
"enterprise": {..., "jarvis_chat", "jarvis_voice"}
```

### C2: Display names en `TenantInfoCard.tsx`

```
freemium/starter → "Pulso Básico"
growth → "GPS Financiero"
enterprise → "Contexia Total"
```

### C3: Messaging en `UpgradePlanBanner.tsx`

Copy con pricing y feature unlock específico.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Hermes gateway offline | Cron falla, alert a Slack, retry 3 veces |
| Manus timeout | Brief omite sección comercial, envía parcial |
| Telegram token expuesto | En Bitwarden, rotar antes de deploy |

---

## Dependencias

```
Stage 0 (Prerequisites) → Fase A → Fase B → Fase C → Stage 11 (Deploy)
```

---

## Re-scope 2026-09-13 — decisiones D1-D13 (`HANDOFF.md`)

El hilo del 2026-09-13 encontró Fase A parcialmente implementada con un **segundo bot de
Telegram** (`TELEGRAM_BOT_TOKEN_JARVIS`, commit `45fd4af`) y Fase C con cambios reales sin
commitear en el working tree. Estas decisiones del fundador, tomadas ese día, **reemplazan** las
secciones D1-D4 originales de arriba donde entren en conflicto (arquitectura del brief matutino
sigue vigente; el canal de Telegram cambia):

### D1: Un solo bot de Telegram (reemplaza el segundo bot de Fase A)

**Decisión:** fusionar la lógica del webhook de `jarvis_endpoints.py` dentro del webhook
existente de `telegram_endpoints.py` (bot de Taty, `TELEGRAM_BOT_TOKEN`). Antes del lookup en
`telegram_chat_mappings`, comprobar `str(chat_id) == TELEGRAM_JUAN_DAVID_CHAT_ID` → ruta Jarvis
(proxy a Hermes con contexto admin); si no → flujo actual de Taty. Eliminar
`TELEGRAM_BOT_TOKEN_JARVIS` y `TELEGRAM_WEBHOOK_SECRET_JARVIS`. Conservar
`/api/v1/jarvis/chat`, `/status`, `/brief` (SSE, backend) sin cambios.

**Por qué:** un bot que administrar, un secreto, un webhook. Costo de migración cero porque el
segundo bot nunca se llegó a crear en BotFather (Stage 0.1 original nunca se ejecutó).

### D2: WhatsApp — un solo número, cerebro más profundo para quien lo paga

**Decisión:** en la ruta de respuesta de WhatsApp, si el tenant del lead tiene
`plan_tier ∈ {growth, enterprise}` → proxy a Hermes (contexto del tenant); si no → Taty básica.
Generaliza la Fase D original del proposal al canal que ya existe, sin infraestructura nueva.
Ver Decisión #19 de `ARCHITECTURE.md` ("WhatsApp es un canal de Taty, no un segundo agente").

### D3: El Jarvis personal del fundador se queda en Telegram, nunca en el número de WhatsApp de clientes

**Decisión:** el acceso admin total (Jarvis personal) no se mezcla con el canal público de
WhatsApp — ampliaría la superficie de seguridad sin beneficio.

### D4: Burbuja Jarvis en el PWA (nuevo — no existía en el proposal original)

**Decisión:** burbuja flotante en `contexia-app/app/app/(shell)/layout.tsx`, un solo punto que
envuelve overview/fiscal/flujo-detalle/patrimonio/radar. **No** un quinto ícono en `BottomNav.tsx`
(ya tiene 4: Pulso, Fiscal, Radar, Config). Llama al mismo `POST /api/v1/jarvis/chat`.

### D5: Mini-visualizer, no pantalla completa

**Decisión:** indicador animado pequeño con estados `escuchando / pensando / respondiendo` en la
burbuja del PWA. Explícitamente **NO** la versión de pantalla completa tipo "circuit board".

### D6: Búnker Agentic OS y burbuja PWA comparten `jarvis-client.ts`

**Decisión:** Fase B (Búnker) sigue en alcance y usa el mismo cliente TypeScript que la burbuja
del PWA (D4). Búnker = vista completa (HermesStatusCard, CronJobsMonitor, chat de pantalla
completa); PWA = burbuja cotidiana. Backend construido una vez, dos superficies.

### D7-D13

Decisiones sobre memoria persistente por tenant, agente de voz de venta (LiveKit), alcance de
Gemini, patrones explícitamente no adoptados, gate de consentimiento de voz clonada, y
onboarding B2B por WhatsApp (documentos) quedan registradas en `HANDOFF.md` §2 (tabla completa
D1-D13) — son diseño para hilos futuros de este change o de changes hermanos, no bloquean la
Fase 0-1 (Telegram, este hilo). No se duplican aquí para evitar que `design.md` y `HANDOFF.md`
diverjan; `HANDOFF.md` es la fuente para D7-D13 hasta que una fase que las implemente las
promueva a esta sección.

---

## Re-scope 2026-09-14 — "Jarvis-Hermes" como proyecto propio, dos Jarvis distintos

Conversación en vivo con el fundador, disparada por investigar por qué `setWebhook` se
limpiaba solo (ver hallazgo abajo). Cambia el marco de las Fases 1/D/E de arriba —
**no las revierte, las re-encuadra dentro de un proyecto más grande** que el fundador quiere
nombrar "Jarvis-Hermes", combinando "lo mejor de los dos mundos" (Hermes + el framework Jarvis)
para dar un servicio hiperpersonalizado, distinto de un chat de WhatsApp genérico, coherente con
el posicionamiento de Contexia como "forma contable automatizada con un asistente de esta
calidad".

**D14 (confirmado):** son **dos Jarvis distintos**, no uno solo con contexto variable:
- **Jarvis admin** (el fundador, Juan David) — Telegram, acceso completo a todos los tenants y
  operaciones. Es el que D1/D3 ya describen arriba.
- **Jarvis cliente** — PWA, scoped estrictamente al tenant del cliente que pregunta. Comparte
  infraestructura Hermes/framework Jarvis con el admin, pero nunca comparte contexto ni acceso
  cross-tenant. Esto es una extensión del alcance de D2 (hoy D2 solo cubre WhatsApp para
  growth/enterprise) — el fundador quiere que la **PWA** sea la superficie principal de esto
  para "clientes ya ganados", reemplazando el acceso directo a WhatsApp en el header.

**Hallazgo real que disparó esta conversación — CONFIRMADO, no resuelto:** el bot de Telegram
que este repo llama "Taty" (`TELEGRAM_BOT_TOKEN`) es el **mismo bot que Hermes ya usa** para su
propio canal de Telegram, activo por *long-polling* (`getUpdates`) desde 2026-09-09 (verificado:
`gateway_state.json` → `"telegram":{"state":"connected", "updated_at":"2026-09-09T05:48:22"}`;
el token en `hermes/profiles/contexia/.env::TELEGRAM_BOT_TOKEN` coincide byte a byte con el de
Railway). Telegram solo permite un modo de entrega por bot (webhook o polling, nunca ambos) — un
`setWebhook` hecho por esta sesión hacia el endpoint de Railway se limpiaba solo en minutos,
consistente con que Hermes lo resetea al reconectar para garantizar su propio polling.

**Implicación no resuelta, más allá de Jarvis:** si Hermes lleva desde el 9 de septiembre
compitiendo por este bot, es posible que mensajes reales de clientes onboardeados que le
escriben a "Taty" por Telegram (Decisión #16 de `ARCHITECTURE.md`, per-tenant profiles) hayan
sido drenados por el polling de Hermes antes de que el webhook de `telegram_endpoints.py` los
viera. **No investigado ni cuantificado todavía** — el fundador decidió explícitamente dejar el
polling de Hermes como está por ahora (no tocar) mientras se define el diseño completo de
Jarvis-Hermes, en vez de arreglar el conflicto de inmediato.

**Consecuencia directa para Fase 1 (D1) de este change:** el código ya escrito
(`telegram_endpoints.py::_route_to_jarvis`, commit `f0da981`) es correcto pero **no puede
verificarse en vivo mientras el webhook siga siendo limpiado por Hermes** — el smoke test
(tarea 8) queda bloqueado hasta que el diseño de Jarvis-Hermes resuelva qué proceso posee el
bot. No revertir ese código; es la base correcta para cuando el conflicto se resuelva.

**Pendiente de decisión del fundador (no inventar mientras tanto):**
- Nombre/alcance formal del "proyecto Jarvis-Hermes" — ¿es un change de OpenSpec nuevo, o una
  ampliación de este mismo (`hermes-jarvis-contexia`)?
- Mecanismo técnico para el Jarvis-cliente en la PWA con "todos los agentes de Hermes" —
  acceso a agentes específicos de Hermes desde un cliente externo es una superficie nueva,
  no cubierta por el `/api/v1/jarvis/chat` actual (que ya es tenant-scoped pero no expone
  "agentes" plural, solo un chat proxy a Hermes).
- ~~Cambio de header del PWA~~ — **hecho 2026-09-14**. El fundador mandó la captura de
  referencia (header desktop: nav · logo · tarjeta Taty · Cerrar Sesión). Implementado en
  `ClientTopBar.tsx`: la tarjeta de Taty (WhatsApp, desktop Y mobile) y el botón hamburguesa
  (☰, mobile, nunca tuvo `onClick`) se reemplazaron por `<JarvisBubble variant="desktop|mobile" />`
  — mismo componente de Fase E, ahora con dos instancias (una por breakpoint, seleccionadas vía
  clases responsive, igual que la tarjeta de Taty que reemplazan) en vez de una burbuja flotante
  separada. La burbuja flotante standalone se quitó de `(shell)/layout.tsx`. El panel de chat
  ahora se ancla debajo del header (`top-[112px]`/`top-[92px]`) en vez de la esquina inferior.
  Para un tenant freemium/starter (`hasJarvisChat=false`) el slot queda vacío — sin Taty, sin
  Jarvis — mismo comportamiento honesto que el resto de gating por plan de este repo, pero es
  una regresión real de acceso a soporte para esos clientes que el fundador no abordó
  explícitamente; anotado para que decida si necesitan otro canal. Verificado en el navegador
  (desktop 1280px + mobile 375px): el círculo aparece solo para admin/growth/enterprise, abre
  el panel sin colisión con "Cerrar Sesión" ni con el BottomNav, y el toggle open/close funciona.

## Re-scope 2026-09-15 — badge JARVIS: rediseño visual, renombre, y arreglo de navegación desktop

Sesión de iteración visual en vivo con el fundador sobre el badge de `ClientTopBar.tsx`
(Fase E / re-scope 2026-09-14 de arriba). Cambios reales, verificados en el navegador en cada
paso (mobile 375px y desktop ~975px):

**Typo corregido — "JARVOS" nunca fue el nombre real.** Todo el componente (`aria-label`,
título del panel, placeholder, keyframes CSS `jarvos-*`) decía "JARVOS" por un error de tipeo
en una sesión anterior. Renombrado a **JARVIS** en `JarvisBubble.tsx` y `globals.css` — las
únicas referencias que sobreviven a "jarvos" son al nombre literal de la carpeta externa
`design_handoff_jarvos_header_circle/` (typo real en el nombre del directorio de diseño, fuera
de este repo, no se renombra).

**Anillos HUD, en dos rondas.** Ronda 1: se agregaron capas decorativas extra (anillo punteado
externo, anillo "digital block") sobre las tres capas base del handoff — resultó en un look
"gris/apagado" que no se parecía al diseño de referencia J.A.R.V.I.S. Ronda 2 (rediseño real):
se retiró el anillo que invadía el hueco deliberado entre el anillo intermedio (r=33) y el
contorno (r=41) del handoff, y se agregó un anillo grueso "incandescente" (r=52, stroke 5,
`#99F6E4`, con `<filter>` de blur real vía `feGaussianBlur` — no solo un halo de CSS) fuera de
la anatomía original del handoff, más un anillo tenue de contexto (r=58). Los tres layers
propios del handoff (r=28/33/41) quedan **exactamente** con los valores de spec — nunca se
retonaron. Se agregó rotación lenta a cada anillo (22s/24s/29s/34s, periodos sin múltiplo común
corto) más una animación "harmonic" constante (`jarvis-harmonic`, 5.2s, scale+translateY) para
que el badge respire incluso sin interacción, no solo al presionar.

**Tamaño del badge, en tres rondas** (72/88 handoff → 96/120 → 128/156 header → 96 en el
sidebar de escritorio, ver abajo) — cada ronda vino con un agrandamiento correspondiente del
propio header (`ClientTopBar.tsx`) para darle espacio, hasta terminar reduciéndolo de nuevo
(ver el punto del sidebar).

**Mark del badge reemplazado y re-procesado.** El PNG original (`jarvis_mark.png`, recortado de
`logo_official.png`) se reemplazó por un archivo más nuevo (`Pin.png`, aportado por el
fundador) que traía fondo negro sólido, no transparente — se le quitó el fondo con flood-fill
(BFS desde los bordes, tolerancia sobre canal máximo ≤34) para dejarlo con alpha real antes de
usarlo, evitando el recuadro negro que el fondo original mostraba dentro del núcleo oscuro del
badge.

**Regresión real encontrada y corregida — navegación de escritorio.** Quitar los links de
navegación del header (pedido del fundador, sesión 2026-09-14) asumía que `BottomNav.tsx` ya
cubría ambos breakpoints — nunca lo hizo (`md:hidden`, siempre mobile-only). Resultado: en
escritorio no había NINGUNA forma de llegar a Fiscal/Radar/Patrimonio/Config salvo tecleando la
URL. Fix: `components/layout/DesktopSidebar.tsx` (nuevo) — sidebar fijo a la izquierda,
`hidden md:flex`, con los mismos 5 destinos que `BottomNav` (Patrimonio incluido — el mobile
tampoco lo tenía, se agregó ahí también el mismo día por el mismo motivo). `ClientTopBar`
recibió un prop `sidebarOffset` para (a) correr su propio centrado al espacio a la derecha del
sidebar y (b) achicar el header a una barra delgada en desktop una vez que el badge se movió
*dentro* del sidebar (ver el siguiente punto) — `flujo-detalle/layout.tsx` no pasa este prop
porque nunca tuvo sidebar, y conserva el badge en su propio header sin cambios.

**El badge se mudó al sidebar en desktop, mismo componente, sin acceso nuevo.** Pedido explícito
del fundador: "usa el mismo badge... no crees otro acceso". `JarvisBubble` ganó un prop
`panelAnchor?: "header" | "sidebar"` que solo cambia dónde abre el panel de chat en desktop
(centrado bajo el header vs. al lado del sidebar) — la lógica de gating/estados es la misma
instancia de componente, solo un `size` más chico (96) y otra posición. En mobile el badge
sigue en el header, sin cambios.

**"Cerrar Sesión" — reubicado, sin duplicados.** Se sacó del cluster derecho del header
(`ClientTopBar.tsx`) y se creó `components/layout/SignOutFooter.tsx`, montado al final del
`<main>` en `(shell)/layout.tsx` y en `flujo-detalle/layout.tsx` — mismo botón en toda pantalla,
mobile y desktop. Esto expuso dos duplicados preexistentes que nadie había notado: el botón rojo
`Cerrar sesión` propio de `config/page.tsx`, y el botón flotante `Salir` (mobile-only) propio de
`overview/page.tsx` — ambos existían porque, antes de esta sesión, el único logout de escritorio
vivía en el header y esas dos pantallas se las habían arreglado por su cuenta. Ambos se
eliminaron; `SignOutFooter` es ahora la única fuente. Color corregido en el camino: el primer
intento de `SignOutFooter` usaba texto casi negro (`#020617`) sobre fondo teal — feedback del
fundador ("no negras") — se re-estilizó para calzar con la convención que "Salir" ya usaba
(texto+borde teal sobre fondo oscuro), unificando el estilo en vez de inventar uno nuevo.

**Núcleo del badge — mismo color que el resto de la app.** El relleno del núcleo (`#111D2E`,
valor del handoff) era una navy ligeramente distinta al fondo real de la app
(`#0F172A`, `bg-bg-obsidian`) — casi idéntico en teoría, pero se notaba como un "hueco" más
negro que el resto de la UI, sobre todo bajo el filtro `grayscale`/`brightness` del estado "no
disponible". Se cambió a `#0F172A` exacto.

**"¿Qué es Contexia?" (Config → Ayuda) apuntaba a `/landing.html`, 404 en local.** Ese archivo
vive en la raíz del repo (fuera de `contexia-app/public/`), así que el servidor de desarrollo de
Next no lo sirve — nunca se confirmó si funciona en producción (Vercel sí serviría ese archivo
estático), pero de todos modos era la landing pública de marketing completa (1483 líneas, SEO/
schema.org), no un "acerca de" liviano para un usuario ya autenticado. Se creó
`app/app/(shell)/acerca/page.tsx` — pantalla estática breve (sin fetch, cumple la regla mock-first
de `contexia-app/CLAUDE.md`) con copy tomado de `.antigravity/GROUND_TRUTH.md` (Pulso Diario,
Centinela Fiscal, Radar Predictivo, Auditoría Sombra + la aclaración de que Contexia es
tecnología, no firma contable) — el link de Config ahora apunta ahí.

**Pendiente, no bloqueante:** verificar en producción real (con login real, plan pagado o rol
admin) que el badge se ve a color — todo lo de arriba se verificó en el preview local
simulando `isAdmin=true` vía una cookie JWT falsa (nunca una credencial real), porque el backend
de Railway no es alcanzable desde el dev server local.

## Próximo: Spec (detalla qué código escribir por tarea)
