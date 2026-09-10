# Handoff → hilo GTM (2026-09-10)

**Propósito**: pegar este documento como primer mensaje del hilo de GTM para que arranque con
todo el contexto de los últimos 3-4 días, sin reconstruirlo. Convención: cada afirmación va
marcada `HECHO` (verificado en vivo), `EN PROGRESO`, `PENDIENTE`, `ROADMAP` o `HIPÓTESIS` — regla
que ya trae el propio kit de GTM (`CLAUDE.md.fragment.md`) y que esta sesión ya venía aplicando.

**Urgencia que gobierna todo lo que sigue**: quedan ~1,5 meses de temporada de declaración de
renta persona natural (DIAN cerró cohortes hasta el 26-oct-2026). El objetivo es la **primera
venta ciclo completo hecha por los agentes** (Juan David + Hermes + Claude Code + Taty +
Tatiana + Manus), no solo tener el motor construido.

---

## 1. HECHO — verificado en vivo, no solo desplegado

### Esta sesión (motor de precios + Taty)
- `pricing-quote-engine` + `pricing-catalog-and-operator-quote` + `taty-pricing-skill`: motor de
  pre-cotización, catálogo oficial único (`apps/backend/core/pricing_catalog.py`), y Taty diciendo
  precios reales en todo canal en vez de negarse a cotizar. **Verificado con conversación WhatsApp
  real** (capturas de Chatwoot): Taty dijo *"GPS a $249.000/mes, Contexia Pro desde
  $1.490.000/mes"* y las tres bandas de Entidad A correctamente, y ante *"Solo tengo 300"* ofreció
  Pulso gratis en vez de inventar un descuento.
- Fix en vivo: "Contexia Pro" decía `$1.490.000/mes` sin la palabra "desde" (es el piso de la
  banda Estándar, no un precio fijo) — corregido con `SoftwareTier.starts_from`, desplegado.
- Migración `0048` (tabla `uvt_values` + `b2b_clients.service_band`) aplicada en producción con
  aprobación explícita del fundador.
- Precios oficiales completos (única fuente: `apps/backend/core/pricing_catalog.py`):

  | Línea | Oferta | Precio |
  |---|---|---|
  | Entidad B (software) | Pulso | $0 |
  | Entidad B | GPS | $249.000/mes |
  | Entidad B | Contexia Pro | desde $1.490.000/mes |
  | Entidad B | Contexia Total | cotizado |
  | Entidad A (servicio) | Micro | $890.000 fijo |
  | Entidad A | Estándar | $1.490.000–$2.400.000 |
  | Entidad A | Complejo | cotizado, sin techo publicado |
  | Entidad A | Renta Natural | desde $350.000, según trámites/movimientos/patrimonio |

### Últimos 3-4 días (otras sesiones, confirmado por commits en `main`)
- `b2c-social-lead-capture`: endpoint público de captura + landing `/renta-natural` — desplegado.
- `taty-followup-cadence`: seguimiento de 14 días a leads de WhatsApp sin respuesta.
- `taty-voice-outbound-calls`: infraestructura de llamada saliente vía Twilio (voz genérica, no
  VoiceBox — ver más abajo).
- `taty-document-collection-wiring`: recolección real de documentos por WhatsApp — **este es el
  `active` actual en `feature_list.json`**.
- `voicebox-local-voice-adoption`: VoiceBox integrado y **APAGADO** (`VOICE_ENABLED=false`) —
  bloqueado por consentimiento pendiente de Tatiana Barbosa para su voz clonada (ver §3).

---

## 2. EN PROGRESO — investigación activa de otra sesión, léela antes de tocar Hermes

`openspec/changes/hermes-claude-code-mcp-bridge/` acaba de resolver hechos que cambian lo que
cualquiera asuma sobre Hermes. **Esto es exactamente lo que necesitas para "replicar las skills
en Hermes también"** — no partas de cero:

- La config real y viva del perfil `contexia` es
  `/home/contexia/.hermes/profiles/contexia/config.yaml` (WSL) — **no** `~/.hermes/` a secas
  (eso es un clon de código fuente del propio Hermes Agent, no runtime).
- Hermes corre **10 perfiles** (`approval-queue`, `auditoria`, `centinela`, `contexia`, `kb`,
  `orchestrator`, `pulso`, `radar`, `social-ops`, `taty`), y solo **uno tiene gateway activo**
  (`contexia`, pid propio) — los otros 9 corren como sub-agentes de ese gateway, no como procesos
  independientes. Esto importa: una skill "para Hermes" probablemente se instala en el perfil
  `contexia` y se propaga, no en cada perfil por separado.
- Se encontró una actualización de Hermes interrumpida a medio aplicar (94 revisiones atrás,
  `0.21.1` instalado) — causa raíz de un aviso de módulos mixtos. Resolverlo probablemente es
  prerrequisito antes de instalar nada nuevo (AgentReach, Clay) sobre Hermes.

**Antes de escribir una sola skill nueva para Hermes en el hilo de GTM**: lee el `design.md` y
`tasks.md` completos de ese change y sigue desde donde quedó, no reinventes la exploración.

Otros changes abiertos sin archivar, relevantes al pipeline de ventas por WhatsApp:
- `taty-channel-consolidation` — dos implementaciones de "Taty responde WhatsApp" coexistían;
  solo una puede ser el canal vivo (Meta permite un solo callback URL).
- `whatsapp-durable-inbox` — Tatiana no tenía bandeja real en Chatwoot para mensajes entrantes.
- `taty-wompi-entidad-a-remittance` — el merchant-of-record de Wompi es Entidad B, pero Renta
  Natural es un servicio de Entidad A; hay que resolver cómo se remesa el cobro.

---

## 3. PENDIENTE — tuyo, no bloqueante para el hilo GTM pero sí para escalar

- **11 clientes B2B sin `service_band` registrada** — nadie anotó bajo qué banda se cotizó cada
  honorario histórico; adivinarlo por el monto es justo la inferencia que el motor de precios
  existe para eliminar.
- **`TenantInfoCard.tsx` / `UpgradePlanBanner.tsx`** tienen nombres comerciales que se desviaron
  de los oficiales — el catálogo ya les da una fuente a la cual alinearse.
- **Consentimiento escrito de Tatiana Barbosa** para su voz clonada (VoiceBox) — sin eso el flag
  de voz no se enciende, punto.
- **`evaluate-omniroute-backend-integration`** — evaluación formal pendiente, no aprobada por
  extensión.
- Dos sesiones concurrentes trabajando en el mismo directorio compartido causaron colisiones de
  branch dos veces esta semana (recuperadas sin pérdida de trabajo) — si el hilo GTM también va
  a tocar código, pide un worktree propio desde el inicio.

---

## 4. El GTM Operating Kit que trajiste (ChatGPT, 10-sep-2026)

Ubicación: `C:\Users\contexia\Documents\Codex\2026-09-10\realtime-voice-chat-2\outputs\contexia-gtm-claude-code\`

Ya leído completo esta sesión: `README.md`, `PLAYBOOK.md`, `GUIONES.md`, `REFERENTES.md`,
`CLAUDE.md.fragment.md`. Resumen de lo que aporta:

- **Playbook**: no "lanzar todo Contexia" — usar Renta Natural como cuña de adquisición con dos
  conversiones independientes (servicio A → opt-in separado y opcional → Pulso/GPS de B). Define
  microsegmentos hipótesis (e-commerce, creadores/exportadores de servicios, agencias IA/tech,
  PyME en digitalización, contador/firma pequeña), score de ICP 0-100, 5 oleadas de campaña
  calendarizadas por cohorte de NIT (10-14 sep hasta 16-26 oct), 6 gates de lanzamiento
  (identidad/entidad, capacidad, claim, precio, privacidad, entrega), métricas diarias/semanales
  y ritmo de operación.
- **Guiones**: fórmula de mensaje, anuncios, landing, triage de Taty (acepta "no sé"), handoff a
  Tatiana, cotización, objeciones, demo, propuesta, seguimiento, referido, y el **paquete
  estructurado que Claude Code debe producir para que Hermes lo despache a Manus** (YAML de
  campaña + YAML de respuesta de ejecución con telemetría).
- **Referentes**: consejo de 6 lentes (April Dunford, Pete Kazanjy, Felipe Otálora, David Gómez,
  Aleyda Solís, Brian Balfour) + Jürgen Klaric como filtro creativo final, nunca como método
  troncal ni fuente de "hechos" neurocientíficos.
- **`CLAUDE.md.fragment.md`**: reglas de precedencia de fuentes, gates obligatorios, precios
  (nunca inventar techo, nunca mezclar Entidad A/B), claims prohibidos, privacidad/contacto
  (nada de blast por WhatsApp/SMS/correo, todo requiere aprobación humana), y disciplina de
  `HECHO`/`INFERENCIA`/`HIPÓTESIS`/`DECISIÓN PENDIENTE` — **coincide exactamente con la
  disciplina que esta sesión ya aplicó al motor de precios**: fuente única, nunca inventar un
  número, declarar lo que no se puede ver en vez de estimarlo.

**Verificado, no asumido**: el kit cita el catálogo de precios canónico correctamente (`desde
$350.000`, `desde $1.490.000`, bandas exactas) — coincide con `apps/backend/core/pricing_catalog.py`
verificado en producción. Fecha de corte del kit (9-sep) es un día antes de este handoff; no hay
drift detectado.

**Instalación que el kit pide, todavía no ejecutada**:
1. Copiar `.claude/skills/` del kit al repo real.
2. Fusionar (no reemplazar) `CLAUDE.md.fragment.md` con el `CLAUDE.md` real del repo.
3. Completar `templates/CURRENT-PROCESS-MAP.md` con el flujo real Hermes/CRM/Taty/aprobaciones.
4. Completar `templates/CAPABILITY-REGISTRY.md` — marcar qué es `LIVE_VERIFIED` vs `PILOT_ONLY`
   vs `ROADMAP` (el catálogo de precios y Taty ya calificarían `LIVE_VERIFIED`; Radar Predictivo
   el propio playbook ya lo marca como pantalla con datos de ejemplo — no vender).
5. `/contexia-readiness` antes de generar cualquier pieza comercial.

**Corrección explícita a la instalación propuesta**: el kit dice "skills invocables desde Claude
Code" — pero según lo confirmado en §2, el sistema real tiene a Hermes como orquestador con
gateway propio y perfiles. Las skills del kit (`/contexia-readiness`, `/contexia-renta-campaign`,
`/contexia-manus-package`, etc.) deben quedar **dobladas**: una interfaz invocable desde Claude
Code (ya prevista) y una equivalente accesible desde Hermes (Desktop, dashboard, o Telegram) para
poder correr el ciclo completo sin depender de que Claude Code esté abierto. Cómo se hace esa
segunda mitad depende de lo que `hermes-claude-code-mcp-bridge` termine de resolver — no
inventarlo en paralelo.

---

## 5. Capacidades nuevas a evaluar — del video de YouTube

Fuente: [transcripción del video de Jack (Agent Reach + Clay.com)](https://www.youtube.com/watch?v=yOZVYw9FIWc&t=440s)
y [workspace de Clay](https://app.clay.com/workspaces/1235868/home).

**HIPÓTESIS, no decisión tomada** — ninguna de las dos se instaló ni evaluó todavía:

### Agent Reach (repo open-source, ~32k+ estrellas según el video — cifra del video, no
verificada independientemente)
- Le da a un agente "ojos": scraping/investigación estructurada de YouTube, GitHub, RSS, y con
  cookies del navegador, LinkedIn/Reddit/X. Devuelve texto estructurado en vez de HTML crudo
  (ahorro de tokens real que el video sí demuestra con cifras: ~86k tokens HTML → 2.5x menos con
  extracción estructurada).
- **Fricción con nuestros principios, a resolver antes de instalar**: el método de acceso a
  LinkedIn/Reddit/X vía cookies de sesión personal es exactamente el tipo de cosa que
  `CLAUDE.md.fragment.md` prohíbe para prospección ("no automatizar blasts", "priorizar opt-in").
  El video mismo dice que prefiere no usar ese camino y en su lugar conecta X vía Grok/xAI OAuth.
  **Para Contexia: evaluar solo la mitad de Agent Reach que no depende de cookies de sesión
  personal** (YouTube, GitHub, RSS, búsqueda web estructurada) — coherente con la regla de
  soberanía de datos que ya rige Hermes/GBrain/VoiceBox (nunca depender de credenciales de
  terceros no auditables).
- **Doblado a Hermes y Claude Code, no solo uno**: mismo principio que §4 — si se adopta, debe
  quedar disponible desde ambas superficies. Dado que Hermes ya corre 100% local/on-prem por
  soberanía de datos, Agent Reach como *research OS local* encaja mejor con Hermes que con
  Claude Code (que corre en la nube de Anthropic).
- **Por qué "no vamos a comprarle el OS" (tu instrucción explícita)**: la idea no es depender de
  un producto externo como research OS permanente, sino usar el patrón (enrutamiento inteligente
  + fallbacks + salida estructurada) para eventualmente construir la versión propia de Contexia —
  **"porque también lo vamos a hacer para nosotros mismos"**: esto es una pista de producto
  futuro (Contexia ofreciendo investigación de leads/clientes como capacidad propia, soberana,
  vendible), no solo una herramienta interna. Anotarlo como idea de producto a explorar en el
  hilo GTM, no como compromiso de build.

### Clay.com
- Plataforma de enriquecimiento de leads (usado por HubSpot, OpenAI, Anthropic según el video).
  Se conecta como MCP directo, tanto a Hermes como a Claude Code.
- Contexia ya tiene un patrón de integración de solo-lectura sin escribir de vuelta a terceros
  (ARCHITECTURE.md Decisión #20, HubSpot) — Clay debería seguir el mismo principio si se conecta:
  Contexia **lee/enriquece**, no delega decisiones comerciales a la plataforma.
- **No confundir con HubSpot** (ya integrado, Decisión #20, sync unidireccional Supabase→HubSpot
  en el único pipeline gratis de Renta Natural). Clay sería una capa de enriquecimiento de
  prospección *antes* de que el lead entre al CRM, no un reemplazo.
- Workspace ya existe: `https://app.clay.com/workspaces/1235868/home` — confirmar en el hilo GTM
  si ya tiene datos/tablas configuradas o está vacío.

---

## 6. Canales que el plan debe cubrir — ninguno construido todavía

Explícitos en tu instrucción, ninguno tiene código ni contenido hoy (`ROADMAP`, no `HECHO`):

- Redes sociales orgánicas (contenido del fundador/Tatiana, per Aleyda Solís y Felipe Otálora en
  `REFERENTES.md`).
- Email marketing.
- Video: YouTube, TikTok, Facebook, Instagram.
- Landing page nueva (más allá del `/renta-natural` ya desplegado por `b2c-social-lead-capture`
  — confirmar en el hilo GTM si esa landing ya cubre lo que necesitas o si la "nueva landing" es
  otra distinta).
- La transcripción del video de YouTube que pegaste es, en sí misma, un ejemplo de investigación
  inteligente de leads adaptable a Contexia (temática Agent Reach) — ya cubierto en §5.

---

## 7. Los jugadores — que ninguno quede fuera del plan

Según la documentación existente del proceso de ventas de Contexia y el kit de GTM:

| Jugador | Rol |
|---|---|
| **Juan David** | founder-led sales (Pete Kazanjy) — primeras conversaciones, receta antes de escalar |
| **Tatiana** | Entidad A, revisión y precio final del servicio profesional, dueña del gate de cotización |
| **Taty** | interfaz conversacional (WhatsApp/Telegram/PWA), triage, nunca fija precio final ni concluye obligación tributaria |
| **Hermes** | orquestador — despacha el paquete aprobado a Manus, corre local/on-prem |
| **Claude Code** | construye brief + copy + assets + claims + experimento, aplica los gates antes de que un humano apruebe |
| **Manus** | ejecutor de Facebook/Instagram/Meta y pauta — no decide estrategia, no autoaprueba, créditos como presupuesto de capacidad no meta de consumo |
| **Búnker** | dashboard/CRM — aprobación humana, telemetría normalizada de vuelta a Claude Code |

El kit ya tiene el contrato YAML exacto para el paquete Claude Code → Hermes → Manus (`GUIONES.md`
§11) y los kill switches (`PLAYBOOK.md` §9.2). No hace falta reinventarlo, solo verificarlo contra
la config real de Manus (3 proyectos existentes, per `reference/MANUS-EXECUTION-CONTRACT.md` del
kit — no leído todavía esta sesión, léelo primero en el hilo GTM).

---

## 8. Primeros pasos recomendados al abrir el hilo GTM

Orden que ya trae el kit (`README.md`), con las correcciones de este handoff incorporadas:

1. `/contexia-readiness` — confirmar qué está `LIVE_VERIFIED` hoy (usa este handoff + el catálogo
   real, no el listado del informe técnico del 29-ago que el propio kit ya marca como desactualizado).
2. Leer `openspec/changes/hermes-claude-code-mcp-bridge/` completo antes de tocar Hermes (§2).
3. Leer `reference/MANUS-EXECUTION-CONTRACT.md` y `reference/TELEGRAM-CONTROL-ROOM.md` del kit —
   no leídos todavía, son directamente relevantes al "correr todo desde Telegram/Hermes Desktop".
4. Fusionar `CLAUDE.md.fragment.md` con el `CLAUDE.md` real (decisión de bajo riesgo, alineada
   con la disciplina que esta sesión ya demostró).
5. `/contexia-renta-campaign` para la oleada vigente (verificar fecha real contra hoy — el kit
   calendariza 10-14 sep como primera oleada, que ya pasó o está corriendo).
6. Evaluar Agent Reach (mitad sin cookies) y Clay como changes OpenSpec propios, con gates de
   soberanía de datos aplicados — no instalar directo.
7. Definir el experimento único a probar primero (regla del kit: una hipótesis, un evento, un
   numerador/denominador, un plazo, un stop) — apuntando a la primera venta end-to-end.

---

## Enlaces de referencia

- Kit GTM completo: `C:\Users\contexia\Documents\Codex\2026-09-10\realtime-voice-chat-2\outputs\contexia-gtm-claude-code\`
- Video (Agent Reach + Clay): https://www.youtube.com/watch?v=yOZVYw9FIWc&t=440s
- Clay workspace: https://app.clay.com/workspaces/1235868/home
- Catálogo de precios (fuente única): `apps/backend/core/pricing_catalog.py`
- Este handoff: `progress/gtm-handoff-2026-09-10.md`
