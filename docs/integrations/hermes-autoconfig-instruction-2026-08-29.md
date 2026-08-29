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

## 8. Cómo reportar de vuelta

Cuando termines de configurar tus crons/roles, reporta en este mismo chat (Hermes Desktop):
qué cron creaste, con qué cadencia, y qué endpoint del backend llama cada uno — en texto claro,
sin valores de token. Si algo del backend no se comporta como este documento dice, repórtalo
como una discrepancia a investigar, no lo "arregles" adivinando — ese tipo de arreglo le
corresponde a Claude Code sobre el repo `antigravity-app`.
