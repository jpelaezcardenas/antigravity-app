# Instrucción para Hermes (pegar completa en el chat de Hermes Desktop, perfil con MiMo)

> Este documento es la fuente de verdad para que Hermes se autoconfigure. No inventes
> arquitectura nueva: todo lo que sigue ya está decidido, construido y desplegado en
> `antigravity-app` (backend Railway `-175a` + Supabase + Vercel). Tu trabajo es configurar
> TU LADO (local/WSL: crons, roles, flujos) para que consuma lo que ya existe — no rediseñar
> el backend, no inventar endpoints, no asumir features que no están confirmadas abajo.

## 0. Quién eres y qué NO debes hacer

- Corres 100% local/on-prem (laptop/WSL) — nunca en Railway/Vercel. Esto es una decisión de
  soberanía de datos financieros, no una limitación técnica a "arreglar".
- NO tienes autoridad para modificar código del backend (`antigravity-app` es un repo aparte,
  gobernado por Claude Code/OpenSpec). Tu rol es orquestar tus propios crons/roles/subagentes
  y hablar con el backend solo a través de los puentes ya construidos (abajo).
- NO inventes un "modo swarm" de 10 roles genéricos. Ya se investigó: ese modo es
  documentación aspiracional de `HERMES_WORKSPACE_CONTEXT.md` que nunca se desplegó de verdad
  — cero carpetas de perfil, cero sesiones tmux. Los roles reales que existen hoy en
  `~/.hermes/agents.yaml` son exactamente 3: `centinela-monitor`, `auditoria-runner`,
  `resolucion-executor`. Si necesitas más roles, créalos con nombres que mapeen a productos
  reales de Contexia (ver §3), no a una plantilla genérica de agencia de IA.
- NO inventes precios, tarifas ni promesas de SLA en ninguna conversación con un cliente — el
  pricing real está en §2, cópialo tal cual, no lo parafrasees hacia arriba o abajo.
- NUNCA escribas un valor de secreto/token/contraseña en un archivo, log, o mensaje que quede
  guardado permanentemente. Nombra la variable (`HERMES_BRIDGE_TOKEN`), nunca el valor.
- Antes de cualquier cron/flujo que escriba datos reales de un cliente (Shadow GL, CRM,
  publicación en redes), el gate humano (HITL) sigue siendo obligatorio — la Approval Queue de
  Contexia es el único punto donde algo se publica de verdad. No la saltes nunca.

## 0.5. Capacidades nativas de Hermes que hoy NO se están usando (investigación 2026-08-29)

Se investigó el repo real de Hermes Agent (Nous Research, `github.com/NousResearch/hermes-agent`,
238k+ stars, actualizado hoy mismo) para confirmar si Contexia le está sacando todo el provecho.
**Respuesta corta: no.** Contexia construyó por fuera, a mano, tres cosas que Hermes ya trae
nativas. Esto no es una crítica al trabajo hecho — es una oportunidad real de simplificar y
ganar resiliencia (self-healing, memoria que mejora sola, paralelización real).

> **Regla de verificación**: lo de abajo es lo que el proyecto upstream documenta que existe.
> Tu fuente de verdad sobre qué está REALMENTE activo en tu instalación es lo que veas en tu
> propio Dashboard (`localhost:9119`) y en el Desktop/TUI — no asumas que una feature está
> encendida solo porque el proyecto la ofrece. Verifica cada punto contra tu propia instancia
> antes de tocar nada, y si algo no coincide, repórtalo como hallazgo, no lo fuerces.

1. **Cron scheduler nativo (`hermes cron`, "Scheduled Automations")** — Hermes trae un
   programador de tareas integrado ("Daily reports, nightly backups, weekly audits — all in
   natural language, running unattended", con entrega directa a cualquier plataforma
   conectada). Contexia hoy usa **Scheduled Tasks de Windows** (`ContexiaHermesManusPoller`,
   `ContexiaChatwootBridge`, `ContexiaHermesHubspotPoller`) como workaround externo — una
   investigación anterior ya había confirmado que `~/.hermes/cron/` existe pero está vacío,
   cero jobs registrados. **Acción**: evalúa migrar estos 3 pollers (y el nuevo cron de Pulso
   Diario insight de §3) al cron nativo de Hermes en vez de depender de Task Scheduler de
   Windows — sobrevive mejor a reinicios de Hermes y es lo que el propio sistema espera que uses.
   No lo migres a ciegas: primero confirma en tu Dashboard si `hermes cron list` ya tiene algo,
   y si migrar rompe algo que hoy funciona, quédate con Task Scheduler para ese caso puntual.

2. **Sistema de Skills auto-mejorables (compatible con el estándar abierto `agentskills.io`)**
   — Hermes crea skills automáticamente después de tareas complejas y las mejora solo con el
   uso ("Autonomous skill creation after complex tasks. Skills self-improve during use").
   Los 3 roles reales de Contexia (`centinela-monitor`, `auditoria-runner`,
   `resolucion-executor`) hoy son entradas estáticas en `agents.yaml`, escritas a mano una vez.
   **Acción**: evalúa formalizarlos como Skills reales de Hermes (no solo roles de config) para
   que entren al loop de auto-mejora — en vez de que tú los reescribas a mano cada vez que algo
   cambia en Contexia.

3. **Subagentes paralelos reales (`Spawn isolated subagents for parallel workstreams`)** —
   Hermes puede lanzar subagentes aislados que trabajan en paralelo, y scripts Python que llaman
   herramientas vía RPC para colapsar pipelines de varios pasos. **Acción concreta para el
   cron de Pulso Diario (tarea #1 de §3)**: si hay N tenants freemium sin Shadow GL, no los
   proceses uno por uno en un loop serial — usa la capacidad nativa de subagentes paralelos
   para calcular y empujar el insight de cada tenant simultáneamente. Esto es exactamente lo
   que el "swarm" debería ser en la práctica — no el modo fantasma de 10 roles genéricos que
   descartamos en §0, sino esta capacidad real y soportada.

4. **Aclaración de una duda pendiente**: lo que ves en el dropdown "Agent Profile" del Desktop
   (`taty-v1`, `centinela-v1`, `pulso-v1`, `radar-v1`, `auditoria-v1`, `kb-v1`, `social-ops-v1`,
   más `contexia` y `default`) **es la feature nativa `/personality` de Hermes** — perfiles de
   enrutamiento de modelo/personalidad, no los roles de ejecución de `agents.yaml`. Son dos
   capas distintas del mismo sistema, ambas reales. El hallazgo de que `taty-v1` sigue en
   `glm-5.2·zhipu` mientras el Taty real de producción (backend) ya migró a Groq por costo
   sigue siendo válido — decide tú si ese personality local necesita el mismo repunteo o si
   solo lo usas para pruebas internas donde el costo no importa.

5. **Memoria agente-curada + búsqueda de sesiones + modelado de usuario (Honcho)** — Hermes
   trae de fábrica memoria persistente que se cura sola, búsqueda FTS5 de conversaciones
   pasadas, y modelado incremental de quién eres a través de sesiones. Contexia construyó
   **GBrain** como un segundo cerebro aparte (esquema propio en Supabase, grafo de
   conocimiento, Dream Cycle). **Esto NO se resuelve solo — es una decisión que le corresponde
   al fundador**: ¿GBrain está indexando algo que la memoria nativa de Hermes no cubre (el
   grafo de `contexia-brain/` y los canon docs de `antigravity-app`), o hay solapamiento real
   que valdría la pena simplificar? No fusiones ni apagues nada por tu cuenta — repórtalo como
   pregunta abierta para el fundador.

6. **Mensajería nativa multi-canal** — el gateway de Hermes soporta Telegram, Discord, Slack,
   WhatsApp, Signal y Email nativamente desde un solo proceso. Contexia usa Telegram
   directamente desde el backend (`TELEGRAM_BOT_TOKEN`) y un bridge custom para WhatsApp vía
   Chatwoot (`apps/chatwoot-bridge`). El bridge de Chatwoot para WhatsApp sigue siendo la
   decisión correcta — da un inbox real con historial y pausa HITL vía etiqueta `bot_off`, algo
   que el gateway nativo de Hermes no reemplaza sin más trabajo — no lo toques. Pero vale la
   pena verificar si el bot de Telegram debería pasar por el gateway nativo de Hermes en vez de
   vivir aparte en el backend, para tener continuidad de conversación cross-plataforma nativa.

## 1. Mapa de sistemas reales (no asumir nada fuera de esto)

| Sistema | Qué es | Quién lo toca |
|---|---|---|
| Backend Railway (`antigravity-app-production-175a`) | FastAPI, Shadow GL, `/api/v1/*` | Solo lectura/escritura vía los endpoints documentados abajo — nunca DB directa |
| Supabase (`kpynymwghfwshvcvevxq`) | Postgres + Auth + pgvector | El backend es el único escritor autorizado de las tablas de producto; tú NO tienes ni debes tener la service-role key |
| HubSpot (portal `51867201`) | 1 pipeline gratis, dedicado 100% a Renta Natural B2C | `apps/hermes-hubspot-poller` (local, tuyo) sincroniza `crm_leads`→Contacts/Deals, unidireccional Supabase→HubSpot. `b2b_clients`→Companies, solo lectura, nunca Deals |
| Chatwoot | Inbox real de WhatsApp (Meta Cloud API), inbox `1` | `apps/chatwoot-bridge` (local, tuyo), reenvía a Taty vía el backend |
| Manus | Genera contenido/copy para Renta Natural | Poller local `ContexiaHermesManusPoller` (Scheduled Task de Windows) — lee `operator_tasks` pendientes del backend, Manus produce, tú reportas el resultado |
| Houston | App de escritorio externa, agente "Vendedor", conecta a HubSpot vía su propio Composio — **solo lectura, lead-scoring/pipeline**. No genera outreach que necesite pasar por tu Content Critic. No requiere ninguna configuración tuya — confirmado y cerrado (`houston-lead-scoring-read-only-bridge`) |
| MiMo | Tu LLM de pago (el que usas para razonar en este chat) | **Riesgo confirmado**: tu `~/.hermes/config.yaml` usa un proxy externo (`token-plan-sgp.xiaomimimo.com`) con `fallback_providers: []` vacío — si ese proxy cae, te quedas sin respaldo pese a tener Ollama local y una key de GLM/ZAI ya configuradas y sin usar. Configura ese fallback tú mismo como parte de este trabajo (no es negociable, es resiliencia operativa) |

## 2. Pricing real — cópialo tal cual, no lo inventes ni lo parafrasees hacia otro número

**Campaña 2 (Contexia SaaS B2B, freemium→pago):**

| Tier | Precio mensual (COP) | Incluye hoy en el producto |
|---|---|---|
| Freemium | Gratis | Solo Pulso Diario |
| Starter | $890.000 | Pulso Diario + Mail-Watcher Bot + Centinela Fiscal (ex-ante) + Taty |
| Growth | $1.490.000 | Todo Starter + Radar Predictivo + elusión lícita + 2 revisiones humanas/mes |
| Enterprise | $2.490.000+ | Todo Growth + Radar de Competitividad + gerente de cuenta + SLA 4h |

Adicionales: Auditoría Sombra/Saneamiento $1.2M–$2.5M (pago único) · Horas extra estratega
$180.000/h.

**Nota técnica real que debes saber**: hoy el backend (`core/plan_features.py`) da a Growth y
Enterprise EXACTAMENTE las mismas features que Starter — el gating técnico fino
(Radar Predictivo solo desde Growth, gerente de cuenta solo Enterprise) todavía no está
implementado en código. Si un cliente Growth/Enterprise pregunta por una feature exclusiva de
su tier y el sistema se la da a un Starter también, es una brecha conocida, pendiente en el
roadmap de Contexia — no la niegues, pero tampoco la prometas como ya cerrada.

**Campaña 1 (Renta Natural, B2C estacional):** diagnóstico inicial GRATIS (vía Auditoría
Sombra/Taty), precio final cotizado caso a caso después del diagnóstico — nunca una cifra fija.
Copy exacto a usar: *"Diagnóstico gratis con tu Auditoría Sombra. Precio de tu declaración,
según tu caso — sin sorpresas, te lo decimos antes de cobrarte un peso."*

## 3. Los "5 pilares" del producto y qué necesitan de ti hoy

| Producto | Estado del backend | Qué necesita de Hermes |
|---|---|---|
| **Pulso Diario** | Shadow GL real (`GET /financials`) ya calcula `caja_real`/`ventas_ayer`/`gastos_ayer` por tenant. Para un tenant freemium SIN Shadow GL (lead nuevo), el backend ya tiene un fallback: `POST /api/v1/agents/pulso-diario/insights` (bearer token = `HERMES_BRIDGE_TOKEN`) acepta que tú empujes un insight calculado, y `/financials` lo sirve automáticamente cuando Shadow GL está vacío. | **Esto es lo que NADIE ha configurado todavía — es tu tarea #1.** Crea un cron/rol tuyo que, para cada tenant freemium sin datos, calcule algo razonable (aunque sea una estimación conservadora basada en lo que el cliente declaró en el alta) y lo empuje a ese endpoint. Sin este cron, el endpoint existe pero nunca se usa. |
| **Centinela Fiscal** | Rol `centinela-monitor` ya existe en tu `agents.yaml`, con actividad real hasta 2026-08-25. El puente MCP `centinela_alerts` ya apunta al backend correcto. | Verificar que el cron de este rol sigue corriendo con la cadencia esperada (ex-ante, antes de que venza una obligación, no después). Si no hay cron activo, configúralo. |
| **Taty** | Un solo cerebro (`TatyAgentService`) para Telegram + PWA + WhatsApp (vía Chatwoot). Ya resuelve el perfil del tenant dinámicamente — no requiere provisioning por cliente. | Nada nuevo de tu lado — solo asegúrate de que `ContexiaChatwootBridge` (Scheduled Task) sigue corriendo (watchdog de 1 min). |
| **Radar Predictivo / Patrimonio** | 100% mock en la PWA hoy — no hay backend real detrás. | Fuera de tu alcance actual — no construyas nada aquí todavía, es deuda de producto pendiente, no una tarea de Hermes. |
| **Auditoría Sombra** | Rol `auditoria-runner` ya existe. El wizard (`contexia-wizard`) ya persiste el lead en Supabase (`leads`) + email interno — confirmado, no hay que rehacer esto. | Verificar que el rol sigue produciendo reportes con la cadencia esperada. |

## 4. Fase 0 — Estado real de los bloqueadores (verificado en vivo, 2026-08-29)

1. **`HERMES_BRIDGE_TOKEN` en Railway** → ✅ YA ESTÁ SETEADO en producción. Verifica que tu
   `.env` local (poller de Manus, y cualquier llamada tuya a `/agents/pulso-diario/insights`)
   usa el MISMO valor — pídeselo al fundador por un canal seguro (Bitwarden), nunca lo pegues
   en este chat ni en ningún archivo.
2. **Constraint `operator_tasks.task_type`** → ✅ YA CORREGIDO (migración `0044`, verificado
   en vivo por Claude Code el 2026-08-29). El insert de `pulso_diario_insight` ya no debería
   fallar. Si lo intentas y falla, repórtalo — sería una regresión nueva, no el bug conocido.
3. **Anomalía de deploy de Railway** (un deploy no completó el cutover ~30 min) → sin
   verificar todavía; no te bloquea a ti, es una revisión de dashboard que le corresponde al
   fundador.

**No hay ningún bloqueador técnico pendiente de tu lado para empezar a operar los cronjobs de
§3.**

## 5. Fase 1 — Campaña 1: Go-live Renta Natural (para la demo de Envigado Emprende)

Estas son acciones operativas, no de código — pero SÍ son tuyas o del fundador, ejecútalas o
recuérdaselas explícitamente si no puedes tú:

1. `git pull` en la máquina del poller de Manus.
2. Cambiar `DRY_RUN=false` en `apps/hermes-manus-poller/.env`.
3. Reiniciar el Scheduled Task `ContexiaHermesManusPoller`.
4. Pegar el mensaje de corrección de posicionamiento en Manus (el gate sigue siendo Modo A:
   Manus produce → Content Critic → Approval Queue → clic del fundador → tú despachas → Manus
   publica — nunca publicación directa sin ese clic).
5. Rotar las API keys de Exa si siguen expuestas de una sesión anterior.
6. Una vez el ciclo corra: confirmar que el Claim Ledger aprueba los hooks con fuentes de
   mercado reconocidas, que el fundador puede aprobar un campaign package real, que tú lo
   despachas, y que Manus publica de verdad — capturar evidencia (screenshot/grabación) por si
   algo falla en la demo en vivo.
7. Higiene: 3 de 4 deals en HubSpot están nombrados con número de teléfono en vez del nombre
   del negocio — renómbralos antes de la demo.

## 6. Fase 2 — Campaña 2: primer cliente freemium/starter real

1. El fundador da de alta al cliente desde el Búnker (`B2bRetainersTab.tsx`) — tier real +
   invite link generado por Supabase, entregado manualmente.
2. Si es freemium con saldo de apertura: confirmar que aparece en su Pulso Diario.
3. Si NO tiene saldo de apertura ni Shadow GL: **aquí es donde tu cron de §3 (Pulso Diario
   insight bridge) entra en acción** — sin él, ese cliente ve una pantalla vacía indefinidamente.
4. Confirmar que `Config` le muestra su tier real, y que un endpoint gated (`liquidity-bridge`)
   le da `not_in_plan` si es freemium.

## 7. Qué NO tienes que resolver ahora (deuda técnica, fuera de tu alcance)

- Diferenciar Growth/Enterprise de Starter en código — es tarea de Claude Code sobre
  `antigravity-app`, no tuya.
- Construir el puente Chatwoot→HubSpot para que Houston vea la clasificación de Taty — quedó
  documentado como gap futuro, no se construye todavía.
- Radar Predictivo/Patrimonio reales — siguen siendo mock, no tienes nada que conectar ahí hoy.
- Rotación de secretos, fusión de 3 PRs de seguridad, retiro de política RLS permisiva sobre
  la Approval Queue, control humano antes de emitir un enlace de pago por Taty, migración de
  re-etiquetado de ~40 alertas, decomiso del backend Railway secundario — todo esto es
  "Horizonte 1" del roadmap oficial (ver §9, informe del Hub de Innovación anexo). Le
  corresponde a Claude Code/el fundador, no es tuyo.

## 8. Contexto de negocio adicional (para que Taty y tus roles nunca inventen nada)

Se anexan dos documentos completos al final de este archivo (§9 y §10) — son fuente de verdad,
no resúmenes tuyos para reinterpretar:

- **§9 — Base normativa de la campaña Renta Natural 2026**: topes UVT oficiales, calendario de
  vencimientos por cédula, régimen sancionatorio, tabla progresiva del Art. 241. Cualquier cifra
  fiscal que Taty o el contenido de campaña mencionen DEBE venir de esta tabla — nunca proyectar
  con la UVT del año equivocado (regla anti-alucinación explícita en el documento).
- **§10 — Informe técnico para el Hub de Innovación (Cámara de Comercio Aburrá Sur)**: estado
  verificado del producto al 21 de agosto de 2026, deuda técnica declarada con nombre propio, y
  el roadmap de 5 horizontes (Horizonte 0 = cerrar el go-live comercial, que es exactamente lo
  que las Fases 1-2 de este documento están operacionalizando). Úsalo para entender el contexto
  completo de negocio detrás de cada cron que configures — no eres solo un ejecutor de tareas
  sueltas, estás cerrando el Horizonte 0 del roadmap real de la empresa.

## 11. Cómo reportar de vuelta

Cuando termines de configurar tus crons/roles, reporta en este mismo chat (Hermes Desktop):
qué cron creaste, con qué cadencia, y qué endpoint del backend llama cada uno — en texto claro,
sin valores de token. Si algo del backend no se comporta como este documento dice, repórtalo
como una discrepancia a investigar, no lo "arregles" adivinando — ese tipo de arreglo le
corresponde a Claude Code sobre el repo `antigravity-app`.

## 12. Protocolo de integración Hermes ↔ Claude Code (mismo repo, mismos estándares)

Se pidió que Hermes y Claude Code trabajen con el mismo estándar sobre `antigravity-app`, que
todo quede documentado, y que ninguno de los dos invente ni diverja del otro. Esto resuelve dos
problemas reales encontrados en la primera ronda de configuración de Hermes (§11 arriba):
Hermes reportó haber creado `HANDOFF-OMNIRROUTE.md`/`OMNIRROUTE_SETUP.md` en `antigravity-app`,
pero esos archivos **no existen en el repo real** (ni local en la máquina de Claude Code, ni en
GitHub) — Hermes aclaró después que están "local, sin push". Eso confirma un riesgo estructural:
Hermes probablemente opera sobre **otro checkout del repo** (su propio clon en WSL), distinto
del que usa Claude Code en Windows. Dos clones del mismo repo, editados por separado, sin un
protocolo claro, divergen — es peor que el problema de "archivos sueltos de sesiones paralelas"
que ya se resolvió varias veces en este proyecto con `git status --short` antes de cada commit.

### Regla dura #1 — GitHub `main` es la única fuente de verdad del código, nunca un checkout local

Ni Hermes ni Claude Code confían en "lo que tengo en mi disco". Antes de decir que algo "está
hecho" en `antigravity-app`:
1. `git status --short` en tu propio checkout — ¿qué tienes sin commitear?
2. `git log --oneline -5 origin/main` (requiere `git fetch` primero) — ¿está eso en GitHub?
3. Si no está en GitHub, **no está hecho** — solo existe en tu disco. No lo reportes como
   completado; repórtalo como "pendiente de push" o, mejor, no lo escribas hasta que sepas si
   debe ir al repo o no (ver Regla #2).

### Regla dura #2 — Hermes NO escribe directamente código ni docs en `antigravity-app`

Esto no cambió respecto al documento original (§0): Hermes sigue sin autoridad para tocar el
repo directamente. Lo que sí cambia es el mecanismo de traspaso, para que quede documentado y
trazable en vez de perderse en un chat:

1. Cuando Hermes necesite que algo cambie en `antigravity-app` (código, doc nuevo, config), NO
   escribe el archivo directamente en su propio clon esperando que alguien lo empuje después.
   En vez de eso, **redacta la propuesta completa** (qué archivo, qué contenido, por qué) y se
   la entrega al fundador en el chat — exactamente como se hizo con los documentos de Houston y
   de Renta Natural 2026 (el fundador los generó, Claude Code los verificó y los persistió en
   `docs/integrations/` con un OpenSpec change de por medio).
2. El fundador pega esa propuesta en Claude Code (aquí, o en una sesión nueva de Claude Code).
3. Claude Code decide si es un **cambio de código** (requiere OpenSpec completo: propose→
   design→specs→tasks→apply con TDD→revisor independiente→Stage 11→archive, igual que los 7
   subdominios del plan freemium) o un **doc de referencia pura** (como este mismo archivo:
   verificación + commit directo, sin necesidad de todo el ciclo OpenSpec si no cambia
   comportamiento del sistema).
4. Nada se considera "terminado" hasta que Claude Code confirma que está en `origin/main` — la
   misma regla de la Regla #1, aplicada al proceso completo.

**Por qué así y no al revés (Hermes empujando directo a GitHub):** Hermes no tiene el harness de
revisión (reviewer independiente, TDD, Stage 11 con verificación en Railway/Vercel) que
`antigravity-app` exige para cualquier cambio real — intentar replicarlo dentro de Hermes sería
reinventar lo que Claude Code ya hace bien. El valor de Hermes es local/operativo (crons,
roles, memoria); el valor de Claude Code es el ciclo de vida completo del código versionado.

### Regla dura #3 — Nunca archivos de handoff sueltos en la raíz del repo

`HANDOFF-OMNIRROUTE.md` en la raíz de `antigravity-app` es exactamente el patrón que este
proyecto **ya eliminó una vez** (memoria de sesión: se borraron `CURSOR_GO_NOW.txt` y
`START_HERE_KEEPER_MIGRATION.txt` de la raíz por ser "handoffs sueltos, nunca versionados,
que generan confusión"). Si Hermes tiene algo que documentar de forma duradera, el lugar es
`docs/integrations/` (como este archivo) o `progress/` (si es un reporte de una tarea puntual
del harness) — nunca un archivo nuevo a nivel raíz.

### Regla dura #4 — GBrain no duplica OpenSpec, lo referencia

Las páginas `omniroute-setup-contexia` y `contexia-hermes-configuration` que Hermes dice haber
creado en GBrain deben apuntar (link) al change de OpenSpec correspondiente una vez exista, no
contener una copia paralela de la misma decisión — evita que GBrain y `openspec/changes/`
cuenten historias distintas de lo mismo.

### Regla dura #5 — Resolver OmniRoute ANTES de seguir integrando, no después

OmniRoute (`localhost:20128`, "476+ modelos gratuitos") es una herramienta que Hermes introdujo
por su cuenta — la instrucción original (§1, fila "MiMo") pedía usar el fallback YA configurado
(Ollama local + GLM/ZAI), no traer una pieza nueva sin nombre previo en ningún documento de este
proyecto. Antes de que esto se considere parte de la integración:
1. El fundador decide explícitamente si OmniRoute se adopta o se descarta — no es una decisión
   técnica de Hermes ni de Claude Code, es una decisión de negocio/infraestructura del fundador.
2. Si se adopta: Hermes entrega la propuesta completa (qué es, qué reemplaza, costo, riesgo) al
   fundador → Claude Code la documenta en `ARCHITECTURE.md` (nuevo container/dependencia
   externa, mismo patrón que cualquier otra pieza de infraestructura) → recién ahí se considera
   parte del stack real de Contexia.
3. Si se descarta: Hermes revierte a usar Ollama/GLM como fallback, tal como decía la
   instrucción original.

### Próximo paso concreto (en orden)

1. El fundador le pide a Hermes el contenido completo (no solo la ruta) de
   `HANDOFF-OMNIRROUTE.md` y `OMNIRROUTE_SETUP.md`.
2. El fundador decide OmniRoute (Regla #5) antes de avanzar con cualquier otra integración.
3. Con esas dos cosas resueltas, el fundador trae el contenido a una sesión de Claude Code (aquí
   o nueva) para que se documente/implemente siguiendo el proceso real de este repo — no antes.

## 9. ANEXO — Base Normativa de Campaña: Declaración de Renta Persona Natural 2026

> Fuente de verdad para cualquier cifra fiscal que Taty o el contenido de campaña mencionen.
> Copiada tal cual del documento original — no reinterpretar los números.

**Rol:** Fuente de verdad normativa de toda la campaña Renta 2026 (Facebook, Instagram, WhatsApp/Taty, Landing Page).
**Fuente íntegra:** `fuentes/informe-renta-2026-fuente.txt` (no modificar; cualquier dato nuevo se valida contra este archivo).
**Contexto fiscal:** Año gravable **2025**, declarado y pagado en **2026**. Ley 2277 de 2022.

---

### 1. Parámetros Maestros (usar en TODO el contenido)

| Parámetro | Valor oficial | Cálculo |
| :--- | :--- | :--- |
| UVT año gravable 2025 | **$49.799** | Res. 000193 de 2024 |
| UVT para sanciones/obligaciones desde 01-01-2026 | **$52.374** | Res. 238 de 2025 (+5,17%) |
| Tope obligatoriedad (Art. 592) | **$69.718.600** | 1.400 UVT × $49.799 |
| Tope patrimonio bruto | **$224.095.500** | 4.500 UVT × $49.799 |
| Sanción mínima (extemporaneidad) | **$523.740** | 10 UVT × $52.374 |
| Techo deducciones cédula general | **$66.730.660** | 1.340 UVT × $49.799 |
| Tope renta exenta laboral 25% | **$39.341.210** | 790 UVT × $49.799 |
| Facturación electrónica obligatoria (personas naturales) | desde **$174.296.500** de ingresos brutos | 3.500 UVT × $49.799 |

> **Regla anti-alucinación:** todo número fiscal en copy, infografía o respuesta de Taty debe venir de esta tabla o de la fuente íntegra. Prohibido "proyectar" topes con la UVT 2026 para criterios de obligatoriedad: los topes del Art. 592 se calculan SIEMPRE con la UVT del año gravable ($49.799).

**Corrección aplicada:** los activos previos de la campaña usaban $73.3M (error: cálculo con UVT 2026). El tope real y oficial es **$69.7M**. Todos los activos deben actualizarse.

### 2. Los 5 Criterios de Obligatoriedad (Art. 592 ET)

Basta **UNO** de estos para que una persona natural esté obligada a declarar, aunque su depuración dé impuesto en cero o saldo a favor:

1. **Ingresos brutos totales** ≥ $69.7M
2. **Compras y consumos totales** ≥ $69.7M
3. **Consignaciones bancarias / depósitos / inversiones** ≥ $69.7M
4. **Consumos con tarjeta de crédito** ≥ $69.7M
5. **Patrimonio bruto al 31-dic-2025** ≥ $224.1M
6. **Cualquier persona natural que haya sido responsable de IVA en 2025** declara sin importar montos.

> **Gancho de campaña #1:** mover plata (consignaciones, tarjeta) es lo que dispara la obligación. Un asalariado que gana $50M pero rota fondos de terceros por su cuenta también está obligado. Esto conecta con el "colombiano promedio".

### 3. Calendario de Vencimientos 2026 (personas naturales)

Presentación y pago entre **12 de agosto y 26 de octubre de 2026**, según los **dos últimos dígitos del NIT/cédula**:

| Últimos 2 dígitos | Fecha límite 2026 |
| :--- | :--- |
| 01 - 02 | 12 de agosto |
| 11 - 12 | 20 de agosto |
| 23 - 24 | 28 de agosto |
| 35 - 36 | 7 de septiembre |
| 55 - 56 | 21 de septiembre |
| 75 - 76 | 7 de octubre |
| 89 - 90 | 19 de octubre |
| 99 - 00 | 26 de octubre |

> **Gancho de campaña #2 (urgencia con fecha):** "Si tu cédula termina en 01 o 02, te queda poco tiempo". El calendario escalonado permite contenido recurrente semanal hasta octubre.

### 4. Régimen Sancionatorio (dolor de campaña)

*   **Extemporaneidad:** recargo del **5% del saldo a pagar por cada mes** (o fracción) de retraso, más intereses de usura fiscal.
*   **Sanción mínima:** **$523.740 COP** incluso si el saldo a pagar es $0 (omisión meramente formal).
*   **Inexactitud:** aplica si hay concurrencia injustificada de costos + renta exenta del 25%.

### 5. Temas Avanzados (usar en contenido educativo, no en hooks masivos)

*   **Sistema cedular (Ley 2277/2022):** cédula general (trabajo + capital + no laborales), cédulas de pensiones, dividendos y ganancias ocasionales. Techo de deducciones recortado a 1.340 UVT.
*   **Independientes (Art. 206, par. 5):** elegir entre costos/gastos soportados con factura electrónica **O** renta exenta del 25% (tope 790 UVT) — mutuamente excluyentes.
*   **Anticipo de renta (Art. 807):** 25% (1ª vez) / 50% / 75% del impuesto previsible, según historial de declaraciones.
*   **Beneficio de auditoría (Art. 689-3):** firmeza acelerada a 12 o 6 meses si el impuesto neto creció ≥25% / ≥35% vs año anterior. No aplica correcciones tardías del año base (Conceptos DIAN 404 y 4223 de 2026).
*   **Renta mundial (Art. 254):** freelancers que trabajan remoto para el exterior tributan en Colombia; el Art. 254 aplica solo a rentas de **fuente extranjera** real (Sentencia 26644 Consejo de Estado: si el trabajo se ejecuta en Colombia, la retención extranjera no descuenta impuesto en Colombia, salvo deducción por Art. 107 ET).
*   **Impuesto al patrimonio:** permanente, umbral 72.000 UVT (~$3.600M+), no relevante para el ICP promedio.
*   **Declaración sugerida DIAN:** el Estado ya tiene la info exógena (bancos, facturas electrónicas, notarías). Mensaje de campaña: "la DIAN ya sabe cuánto moviste".
*   **No residentes:** tarifa plana 35%.

### 6. Tabla Progresiva Art. 241 (referencia para Taty)

| Base gravable (UVT) | Tarifa marginal | Impuesto base acumulado |
| :--- | :--- | :--- |
| 0 – 1.090 | 0% | 0 |
| 1.090 – 1.700 | 19% | (base − 1.090) × 19% |
| 1.700 – 4.100 | 28% | +116 UVT |
| 4.100 – 8.670 | 33% | +788 UVT |
| 8.670 – 18.970 | 35% | +2.296 UVT |
| 18.970 – 31.000 | 37% | +5.901 UVT |
| > 31.000 | 39% | +10.352 UVT |

### 7. Mapeo a Contenido de Campaña

| Tema | Pilar | Gancho coloquial |
| :--- | :--- | :--- |
| Topes Art. 592 | Urgencia/Miedo | "¿Te toca declarar ante la DIAN? Si moviste $69.7M en tu cuenta, sí." |
| Calendario por cédula | Urgencia/FOMO | "Tu cédula termina en 01-02? Vencimiento: 12 de agosto." |
| Sanción mínima | Miedo | "La multa arranca en $523.740 aunque no debas ni un peso." |
| Independientes 25% vs costos | Educación | "¿Cobras honorarios? Este truco del 25% puede ahorrarte millones (pero elige solo una)." |
| Freelancers del exterior | Nicho (freelancers) | "Trabajas remoto para USA/España y te retuvieron impuestos allá? Ojo: en Colombia eso NO descuenta automáticamente." |
| DIAN ya sabe todo | Conciencia | "La DIAN ya ve tus consignaciones y compras con tarjeta. La pregunta no es si sabe, sino si tú estás listo." |

---

*Documento generado por Manus — Proyecto CTX Strategy & Market Intelligence. Mantener sincronizado con el repo antigravity-app (`constants.py`, `kb/dian_chunks.json`) para que Taty responda con estos mismos valores.*

## 10. ANEXO — Informe Técnico para el Hub de Innovación (Cámara de Comercio Aburrá Sur), v3.0, 21-ago-2026

> Contexto de negocio completo. El Horizonte 0 de este roadmap ES lo que las Fases 1-2 de
> este documento operacionalizan. Imágenes del original omitidas (capturas de pantalla de
> Hermes Desktop/Dashboard, no aportan al texto).

Infraestructura, estado verificado y roadmap de construcción

**--- · ---**

**Preparado para el Hub de Innovación**

Cámara de Comercio Aburrá Sur

  --------------------------------------------------
  **Documento**    Informe técnico de
                   infraestructura, estado y roadmap
  ---------------- ---------------------------------
  **Versión**      3.0

  **Fecha**        21 de agosto de 2026

  **Elaborado      Juan David Peláez Cárdenas
  por**            

  **Con la         Tatiana Marcela Barbosa Villegas
  participación    
  de**             

  **Contacto**     jpelaezcardenas@gmail.com
  --------------------------------------------------

*Documento de uso interno para el proceso de acompañamiento del Hub de
Innovación.*

**Contenido**

[1. ¿Qué es Contexia?](#qué-es-contexia)2

[2. Qué construimos: los dos dominios del
producto](#qué-construimos-los-dos-dominios-del-producto)3

[3. Arquitectura técnica](#arquitectura-técnica)3

[4. Estado actual verificado (21 de agosto de
2026)](#estado-actual-verificado-21-de-agosto-de-2026)4

[5. Deuda técnica abierta y riesgos
declarados](#deuda-técnica-abierta-y-riesgos-declarados)5

[6. Hacia dónde vamos: roadmap de
construcción](#hacia-dónde-vamos-roadmap-de-construcción)6

[7. Cómo trabajamos: entorno de desarrollo con agentes
IA](#cómo-trabajamos-entorno-de-desarrollo-con-agentes-ia)7

[8. Enlaces y acceso a la demo](#enlaces-y-acceso-a-la-demo)8

[9. ¿Cómo nos puede ayudar el Hub?](#cómo-nos-puede-ayudar-el-hub)9

[10. ¿Cómo nos puede ayudar el desarrollador
asignado?](#cómo-nos-puede-ayudar-el-desarrollador-asignado)9

[11. Contacto y siguiente paso](#contacto-y-siguiente-paso)10

### **1. ¿Qué es Contexia?**

Contexia es una AAA (AI Automation Agency) y empresa TIC enfocada en
automatización contable-financiera, fintech e inteligencia financiera
aplicada a PyMEs y a negocios digitales.

Contexia opera como la capa tecnológica del ecosistema ---propiedad
intelectual, código fuente, infraestructura de servidores y marca--- y
presta servicios B2B: SaaS, licenciamiento, implementación y
mantenimiento. La fortaleza del modelo es la combinación de tecnología
propia con contadoras públicas tituladas y con tarjeta profesional. El
límite legal se mantiene explícito: **Contexia no es una firma contable
regulada** --- no está adscrita a la Junta Central de Contadores, no
ejerce contaduría pública regulada y no firma estados financieros,
declaraciones tributarias ni dictámenes.

Esa función la cumple Tatiana Marcela Barbosa Villegas, contadora
pública graduada y socia de Juan David en Contexia, a través de la firma
contable registrada (Entidad A), con la que Contexia (Entidad B) se
integra tecnológicamente.

**Qué cambió desde la versión 2.0 (14 de julio de 2026):** este
documento reemplaza al informe anterior. En las seis semanas
transcurridas se cerraron y desplegaron **52 cambios de producto
adicionales** bajo el estándar OpenSpec, el producto pasó de un módulo a
dos dominios, y la brecha de autenticación que el informe v2 declaraba
abierta **quedó cerrada**: la API de datos financieros ya exige sesión
válida. Las secciones 4 y 5 detallan qué está verificado y qué sigue
abierto; la sección 6 es el roadmap de construcción.

### **2. Qué construimos: los dos dominios del producto**

El producto creció de un módulo único a dos dominios que comparten
infraestructura pero no se mezclan: uno mira al cliente, el otro es la
sala de máquinas comercial.

**Dominio A --- GPS Financiero (lo que ve el cliente):**

- **Pulso Diario** --- Caja Real del día, ingresos y gastos del día
  anterior, calculados sobre el libro mayor sombra, no sobre
  estimaciones.

- **Centinela Fiscal** --- vigilancia ex-ante de obligaciones
  tributarias y alertas, aisladas por cliente.

- **Radar Predictivo** --- proyección de flujo de caja y riesgos
  financieros.

- **Auditoría Sombra (Shadow GL)** --- conciliación automática entre lo
  declarado y lo real.

- **Patrimonio y Detalle de flujo** --- desglose estructural de la salud
  financiera.

- **Taty** --- la contadora conversacional 24/7. Un solo cerebro, tres
  canales: la app, Telegram y WhatsApp.

**Dominio B --- Búnker (la sala de máquinas):**

El Búnker es el panel de operación. Es la misma base de código de la app
del cliente, diferenciada por ruta y por rol: el equipo Contexia ve las
siete secciones; un cliente B2B ve solo tres (Dashboard, Agentic OS y
Configuración).

- **CRM y Ventas** --- embudo B2C de Renta Natural y cartera B2B, con
  alertas automáticas de riesgo de fuga de cliente.

- **Sell Machine** --- pipeline creativo: investigación → redacción →
  crítica de marca → cola de aprobación humana → publicación.

- **Social Content Ops y Onboarding** --- operación de contenido y alta
  de clientes nuevos.

- **Agentic OS** --- estado, trazabilidad y control de los agentes.

**Dos líneas de ingreso:** B2B (PyMEs con contabilidad recurrente) y B2C
(Renta Natural para persona natural, temporada 2026, con cobro por
pasarela de pagos).

### **3. Arquitectura técnica**

Stack de producción, de extremo a extremo:

  -------------------------------------------------------------------------
  **Capa**         **Tecnología**           **Función**
  ---------------- ------------------------ -------------------------------
  **Frontend       Next.js 16, React 19,    Una sola base de código: 6
  (app + Búnker)** TypeScript, Tailwind v4  pantallas móviles para el
                                            cliente + 7 secciones de
                                            escritorio filtradas por rol

  **Backend /      Python 3.11, FastAPI     Libro mayor sombra, endpoints
  API**                                     /api/v1/\*, resolución de
                                            cliente por sesión

  **Base de        Supabase (PostgreSQL +   Datos financieros aislados por
  datos**          pgvector)                cliente, autenticación, RLS y
                                            búsqueda semántica del
                                            normograma DIAN

  **Despliegue     Vercel                   Auto-deploy desde main hacia
  frontend**                                contexia.online

  **Despliegue     Railway                  Un único backend canónico,
  backend**                                 auto-deploy desde main

  **Modelos de     Cascada Groq → Cerebras  Failover automático entre
  IA**             → OpenRouter → NVIDIA    proveedores; cascada revisada
                   NIM                      el 18 de agosto de 2026

  **Orquestación   Hermes Workspace (local  Coordina los 9 agentes; los
  de agentes**     / on-prem)               datos financieros se procesan
                                            localmente por soberanía de
                                            datos, nunca en un VPS de
                                            terceros

  **Memoria de     GBrain (local / on-prem) Búsqueda híbrida y grafo de
  agentes**                                 conocimiento del proyecto para
                                            que los agentes no empiecen de
                                            cero en cada sesión

  **Canal          Chatwoot + bridge        Bandeja real de Meta Cloud API;
  WhatsApp**       (local, Docker)          las credenciales nunca salen de
                                            la máquina local

  **CRM            HubSpot + sincronizador  Sincronización unidireccional
  comercial**      local                    cada 5 minutos; capa de
                                            reporte, no reemplazo del CRM
                                            propio

  **Pagos**        Wompi                    Cobro del embudo B2C,
                                            credenciales de producción
                                            activas

  **Secretos**     Bitwarden Secrets        Bóveda única; ninguna
                   Manager                  credencial vive en el código
  -------------------------------------------------------------------------

**Flujo de datos operativo en producción:** ingesta de CSV (Siigo) y XML
(facturación electrónica DIAN) → libro mayor sombra por cliente → API de
datos financieros que resuelve a qué cliente pertenece la sesión →
tablero en vivo. Desde el 18 de agosto cada asiento contable lleva una
bandera de verificación que separa los datos reales de los de prueba,
para que ninguna cifra de demostración pueda confundirse con una cifra
de cliente.

### **4. Estado actual verificado (21 de agosto de 2026)**

Cada punto de esta sección fue verificado contra el sistema en vivo o
contra el repositorio el día de la fecha, no copiado de documentación
previa.

- **Autenticación activa --- cierra la brecha declarada en el informe
  v2:** el backend canónico responde 401 ("token de autenticación
  inválido o ausente") a la API de datos financieros cuando no hay
  sesión. En julio ese endpoint era abierto. Hoy las pantallas cargan,
  pero no muestran cifras sin credenciales.

- **Aislamiento por cliente de extremo a extremo:** un único contrato de
  resolución de cliente gobierna las seis superficies de agentes. Un
  usuario autenticado cuyo cliente no resuelve recibe una respuesta
  vacía o un 404 --- nunca los datos de otro.

- **Login único y control de acceso por rol:** existe un solo punto de
  entrada válido; un middleware en el borde de Vercel valida el token de
  sesión y las rutas de administración exigen rol de administrador.

- **Gobernanza por especificación, con evidencia:** 72 cambios OpenSpec
  archivados con su rastro completo ---propuesta, diseño,
  especificación, tareas, implementación y despliegue verificado en
  producción---. Solo 3 cambios activos, y ninguno bloquea la operación.

- **Cobertura de pruebas:** 116 archivos de pruebas automatizadas en el
  backend.

- **Taty omnicanal en producción:** los mensajes de WhatsApp entran a
  una bandeja real, se enrutan al mismo servicio que atiende Telegram y
  la app, y pueden pausarse con una etiqueta para que responda una
  persona.

- **Motor comercial operativo:** el circuito de contenido
  ---investigación, crítica de marca, cola de aprobación humana y
  publicación--- está cerrado de punta a punta, con un filtro
  determinista que rechaza cualquier cifra en pesos o UVT que no cite
  una fuente reconocida. Hoy corre en modo de ensayo, a la espera del
  interruptor de publicación real.

- **CRM sincronizado:** el embudo B2C se refleja en HubSpot cada 5
  minutos desde un proceso que corre en la máquina local; la
  sincronización es unidireccional y el Búnker solo lee su estado.

- **Presencia digital estructurada:** robots.txt, sitemap.xml y marcado
  Schema.org geolocalizado en Envigado, dirigido tanto a buscadores
  tradicionales como a motores de respuesta con IA.

- **Financiación en curso:** además de la ronda ángel / capital semilla,
  Contexia participa en Envigado Emprende 2026, cuyo plan de inversión
  financia la estación de trabajo de inferencia local descrita en el
  Horizonte 2 del roadmap.

### **5. Deuda técnica abierta y riesgos declarados**

Un informe técnico que solo muestra logros no sirve para pedir ayuda.
Esto es lo que está abierto hoy, con nombre propio y con horizonte
asignado en la sección 6.

  -----------------------------------------------------------------------
  **Ítem**               **Riesgo**                     **Estado**
  ---------------------- ------------------------------ -----------------
  **Rotación de          Credenciales señaladas en la   Vencida \~60
  secretos**             auditoría interna de junio     días. Prioridad
                         siguen sin rotar en su         alta
                         totalidad                      

  **Tres PRs de          27 correcciones de junio nunca Abierto
  seguridad sin          llegaron a producción          
  fusionar**                                            

  **Política de base de  Acceso anónimo residual sobre  Identificada y
  datos permisiva**      la cola de aprobación a nivel  documentada;
                         de RLS                         pendiente de
                                                        retirar

  **Enlace de pago sin   Una rama del flujo comercial   Cambio congelado
  revisión humana**      de Taty puede emitir un enlace a propósito; el
                         de cobro por WhatsApp sin      control está
                         aprobación previa              especificado, no
                                                        implementado

  **Comerciante de       El cobro de un servicio        Decisión
  registro**             contable debe salir de la      estructural
                         Entidad A, no de la Entidad B  pendiente

  **Alertas históricas   \~40 alertas antiguas quedaron Migración
  mal etiquetadas**      asociadas al cliente           escrita, no
                         equivocado                     aplicada;
                                                        requiere
                                                        aprobación
                                                        explícita

  **Backend secundario   Un segundo proyecto en Railway Por decomisionar
  en desuso**            sin tráfico real, con un       
                         chequeo de salud               
                         silenciosamente roto           

  **Tarifas de Renta     Taty tiene prohibido enunciar  Decisión de
  Natural sin definir**  precio mientras no existan las negocio pendiente
                         dos tarifas                    
  -----------------------------------------------------------------------

Ninguno de estos ítems bloquea la operación actual. Todos están
priorizados, y varios son exactamente el tipo de trabajo acotado en el
que el acompañamiento del Hub rinde más.

### **6. Hacia dónde vamos: roadmap de construcción**

El roadmap está organizado en cinco horizontes. Cada ítem corresponde a
un cambio OpenSpec ---existente o por abrir---, no a una intención
general.

**Horizonte 0 --- Cerrar el go-live comercial (agosto -- septiembre
2026)**

- Activar la publicación real del motor de contenido y correr un ciclo
  completo verificable de punta a punta.

- Completar una transacción real de Renta Natural por la pasarela de
  pagos y registrar su referencia.

- Definir las dos tarifas de Renta Natural (asalariado / independiente)
  y cablearlas en el cobro.

- Resolver el comerciante de registro: cuenta de cobro de la Entidad A
  para servicios contables.

- Verificación en producción del cambio de SEO, optimización para
  motores de IA y grafo de conocimiento local.

**Horizonte 1 --- Endurecimiento y confianza (septiembre -- octubre
2026)**

- Rotación completa de secretos y fusión de los tres PRs de seguridad
  pendientes.

- Retirar la política de base de datos permisiva y cerrar las fases
  restantes del aislamiento por cliente.

- Implementar el control humano obligatorio antes de emitir cualquier
  enlace de pago.

- Aplicar la migración de re-etiquetado de alertas y decomisionar el
  backend secundario.

- **Auditoría externa de seguridad y arquitectura** --- aquí es donde el
  acompañamiento del Hub tiene el mayor efecto multiplicador, porque el
  respaldo de un tercero pesa frente a clientes e inversionistas.

**Horizonte 2 --- Nodo soberano de inferencia local (octubre --
noviembre 2026)**

- Adquisición de la estación de trabajo contemplada en el plan de
  inversión: AMD Ryzen 9 9900X, NVIDIA RTX 5060 Ti de 16 GB, 32 GB DDR5,
  NVMe Gen5, refrigeración líquida y UPS con regulación de voltaje.

- Migrar a inferencia local el procesamiento por lotes de datos
  sensibles: conciliación bancaria nocturna, clasificación de
  transacciones, generación de alertas fiscales, embeddings del
  normograma y transcripción de notas de voz.

- Dejar en la nube únicamente lo sensible a latencia ---la conversación
  con Taty---, siempre con anonimización previa al envío, según el
  protocolo interno de seguridad.

- Red, firewall, segmentación, respaldos y monitoreo del nodo local: el
  aporte técnico más concreto que puede hacer el desarrollador asignado.

- Túnel persistente y autenticado entre el Búnker en la nube y el
  orquestador local. Hoy funciona, pero sobre un túnel efímero que hay
  que reconfigurar en cada reinicio.

**Horizonte 3 --- Integraciones de datos reales (noviembre 2026 -- enero
2027)**

- Cliente de integración con Siigo por API REST. Hoy la ingesta se hace
  con el archivo CSV exportado.

- Cliente DIAN (XML UBL 2.1 y MUISCA), primero en ambiente de pruebas y
  luego en producción.

- Evaluar un middleware de terceros que evite la integración directa con
  la DIAN, comparando su costo de instalación y mensualidad contra el de
  construir y mantener la integración propia.

- Con datos reales fluyendo, desbloquear la ingesta masiva del libro
  mayor sombra: un cambio de \~100 tareas ya especificado y hoy en pausa
  por falta de fuente.

**Horizonte 4 --- Escala (2027)**

- Tablero de métricas y observabilidad por agente: costo, latencia y
  trazabilidad de cada decisión.

- Ajuste fino de modelos pequeños sobre patrones fiscales del cliente,
  ejecutado localmente y sin subir datos a ningún proveedor externo.

- De un cliente cero y diez clientes aprovisionados a la primera cartera
  de clientes de pago recurrente.

- Ruta de crecimiento del hardware ya prevista sin cambiar tarjeta madre
  ni fuente: más memoria, segundo disco y GPU de mayor capacidad cuando
  el número de usuarios lo exija.

### **7. Cómo trabajamos: entorno de desarrollo con agentes IA**

Contexia se construye con un flujo de desarrollo agent-first: en el lado
tecnológico, Juan David ---apoyado en agentes--- usa varios copilotos de
código de forma combinada (Claude Code de Anthropic, Codex de OpenAI y
Antigravity de Google) como implementadores, siempre bajo especificación
escrita antes de tocar código.

- **Gobernanza por especificación (OpenSpec):** cada cambio pasa por
  propuesta → diseño → especificación → tareas → implementación →
  despliegue. El despliegue a producción es una etapa obligatoria: nada
  se archiva sin estar en vivo y verificado. Los 72 cambios archivados
  son el rastro auditable de ese estándar.

- **Harness de subagentes:** los cambios se ejecutan con un patrón líder
  → implementador → revisor, para que haya una revisión estructurada
  antes de llegar a producción.

- **Hermes Workspace:** orquesta los 9 agentes operativos del producto.
  Corre local / on-prem, nunca en un VPS de terceros, por la regla de
  soberanía de datos.

- **Modelos de IA:** cascada de proveedores con failover automático
  (Groq, Cerebras, OpenRouter y NVIDIA NIM), revisada el 18 de agosto de
  2026 para operar sobre capas gratuitas mientras el volumen lo permita.
  Para datos financieros sensibles la ruta es inferencia local sobre el
  nodo soberano del Horizonte 2, replicando en la infraestructura propia
  los controles de un entorno cloud: aislamiento de procesos, control de
  salida de red y mínimo privilegio.

- **GBrain (memoria de los agentes):** capa de memoria persistente y
  grafo de conocimiento que consolida contexto, decisiones y entidades
  del proyecto para que los agentes no partan de cero en cada sesión.

- **Investigación y producción de contenido:** los borradores generados
  por agentes de investigación nunca se publican solos. Pasan por el
  crítico de marca y por la cola de aprobación humana en el Búnker.
  Mantener ese control fue una decisión explícita y está documentada.

**Hermes Workspace, en detalle** --- corre local (WSL/Ubuntu), no
expuesto a internet:

  ---------------------------------------------------------------------------
  **Componente**        **Función**                  **Acceso (solo local)**
  --------------------- ---------------------------- ------------------------
  **Hermes Gateway**    API del agente:              127.0.0.1:8644 --- solo
                        orquestación, herramientas,  API, con webhook firmado
                        sesiones y planificador de   
                        tareas interno               

  **Hermes Workspace**  Interfaz de chat con el      http://localhost:3000/
                        agente principal y sus       
                        sub-agentes                  

  **Hermes Dashboard**  Configuración, sesiones,     http://localhost:9119/
                        llaves y observabilidad      
  ---------------------------------------------------------------------------

Como hoy solo es accesible desde la máquina local del equipo, se
incluyen capturas reales de estas dos interfaces a continuación para que
el desarrollador entienda el entorno sin necesitar acceso remoto.

height="2.7395833333333335in"}

*Hermes Workspace --- interfaz web del agente principal (chat, memoria,
herramientas, ejecución en vivo).*


*Hermes Agent --- vista de terminal del agente (herramientas y skills
disponibles, sesión activa, modelo en uso).*

### **8. Enlaces y acceso a la demo**

**Estado actual del acceso --- cambió respecto del informe v2:** la API
de datos financieros ya exige sesión. Sin credenciales, las pantallas
del producto cargan pero no muestran cifras. Para que el equipo del Hub
recorra el producto con datos, creamos una cuenta dedicada con
contraseña que podemos rotar o revocar al terminar el proceso de
asesoría; solo necesitamos el correo del evaluador.

**Canal en vivo que no requiere credenciales:** se puede probar a Taty
ahora mismo escribiendo por WhatsApp al +57 310 622 9289. Es el número
de producción y responde el mismo agente que atiende a los clientes.

**Sitio web público (landing):**

- [[https://contexia.online/landing.html]{.underline}](https://contexia.online/landing.html)
  --- presentación comercial del GPS Financiero y captación de leads

**Portal de acceso (login):**

- [[https://contexia.online/login.html]{.underline}](https://contexia.online/login.html)
  --- único punto de entrada válido; aquí se habilitará la cuenta del
  Hub

**Producto en vivo (requiere sesión):**

- [[https://contexia.online/app/overview]{.underline}](https://contexia.online/app/overview)
  --- Pulso Diario

- [[https://contexia.online/app/fiscal]{.underline}](https://contexia.online/app/fiscal)
  --- Centinela Fiscal

- [[https://contexia.online/app/radar]{.underline}](https://contexia.online/app/radar)
  --- Radar Predictivo

- [[https://contexia.online/app/patrimonio]{.underline}](https://contexia.online/app/patrimonio)
  --- Patrimonio

- [[https://contexia.online/app/flujo-detalle]{.underline}](https://contexia.online/app/flujo-detalle)
  --- Detalle de flujo de caja

- [[https://contexia.online/app/bunker]{.underline}](https://contexia.online/app/bunker)
  --- Búnker; las secciones visibles dependen del rol de la cuenta

**Repositorio técnico (GitHub):** actualmente privado. Con gusto damos
acceso de lectura al desarrollador asignado si nos confirman el usuario
de GitHub a invitar.

### **9. ¿Cómo nos puede ayudar el Hub?**

Puntos concretos donde el acompañamiento institucional del Hub tendría
mayor impacto, ordenados por prioridad real:

- **Auditoría externa de seguridad y arquitectura** antes de sumar más
  clientes (Horizonte 1). Es hoy nuestra mayor necesidad: la revisión de
  un tercero da respaldo frente a clientes e inversionistas.

- **Mentoría técnica** en arquitectura multi-cliente y en el diseño del
  nodo local de inferencia (Horizonte 2).

- **Horas de desarrollador y revisión de código** para acelerar el
  Horizonte 1. Son tareas acotadas y ya especificadas, no exploración.

- **Acompañamiento en la ronda de inversión** ángel o de capital
  semilla: métricas, pitch y materiales.

- **Conexión con PyMEs de la red de la Cámara de Comercio Aburrá Sur**
  como clientes piloto del GPS Financiero.

- **Conexión con otras startups o empresas del Hub** para alianzas,
  clientes cruzados o proveedores.

- **Capacitación empresarial complementaria** (legal y comercial) para
  el equipo fundador, que hoy opera con estructura reducida ---dos
  socios--- apoyado en agentes en el lado tecnológico.

- **Espacio de coworking** o uso de instalaciones de CCAS para el
  equipo.

- **Orientación legal y regulatoria** sobre el modelo dual y, en
  concreto, sobre el comerciante de registro para el cobro de servicios
  contables: es un ítem abierto de la sección 5 y una decisión que no es
  puramente técnica.

### **10. ¿Cómo nos puede ayudar el desarrollador asignado?**

Más allá del acompañamiento institucional, estas son las áreas técnicas
concretas donde el desarrollador asignado puede aportar directamente,
mapeadas contra el roadmap:

- **Seguridad aplicada (Horizonte 1):** cerrar los tres primeros ítems
  de la sección 5 --- rotación de secretos, fusión de los PRs pendientes
  y retiro de la política permisiva de base de datos.

- **APIs (Horizonte 1):** endurecimiento de la API REST ---versionado,
  límites de uso, validación de esquemas y manejo de errores--- y
  revisión del contrato de resolución de cliente.

- **Flujos con humano en el loop (Horizonte 1):** pair programming sobre
  el control de aprobación previo a emitir cualquier enlace de pago.

- **Soberanía de datos (Horizonte 2):** asesoría para replicar
  localmente los controles de un entorno cloud --- aislamiento de
  procesos, control de salida de red y mínimo privilegio.

- **Redes locales (Horizonte 2):** segmentación, firewall y acceso
  remoto seguro para el nodo de inferencia; en particular, reemplazar el
  túnel efímero actual por uno persistente y autenticado.

- **Manejo de servidores (Horizonte 2):** administración y
  endurecimiento del equipo on-prem --- respaldos, monitoreo y
  actualizaciones.

- **Equipos AI-first (Horizonte 2):** validación de la configuración
  adquirida y de la ruta de crecimiento en memoria, almacenamiento y GPU
  a medida que crece el cómputo local.

- **Observabilidad (Horizonte 4):** instrumentación de costo y latencia
  por agente, que es la base del tablero de métricas.

### **11. Contacto y siguiente paso**

**Siguiente paso concreto:** díganos (a) el correo del evaluador para
crear la cuenta del Hub y (b) el usuario de GitHub del desarrollador
asignado. Con esos dos datos queda habilitado el acceso completo
---producto y código--- el mismo día.

**Demo en vivo:** además del acceso directo de la sección 8, con gusto
coordinamos una videollamada para recorrer el producto juntos.

**Contacto:**

- Juan David Peláez Cárdenas --- Fundador (tecnología), Contexia

- jpelaezcardenas@gmail.com, 3504187902

- Tatiana Marcela Barbosa Villegas --- Socia y Contadora Pública,
  Contexia

- tatybarbosav91@gmail.com, 3018948151
