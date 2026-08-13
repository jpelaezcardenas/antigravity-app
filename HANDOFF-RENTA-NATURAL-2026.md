# HANDOFF — Campaña Renta Natural 2026 + Operación B2B en paralelo

> **Uso:** este archivo es el punto de arranque del hilo nuevo. Pega el bloque de §1
> ("Prompt de arranque") en el chat nuevo y adjunta/menciona este archivo. Todo lo demás es
> contexto verificado que el agente debe leer antes de proponer nada.
>
> **Creado:** 2026-08-12. **Estado del repo al crearlo:** commit `8de4dad` en `main`.

---

## 1. Prompt de arranque (copiar y pegar en el hilo nuevo)

```
Hola. Vengo de un hilo dedicado a CRM. Vamos a planear la integración que permita correr la
campaña B2C "Renta Natural 2026" en paralelo con la operación B2B existente, con Manus como
ejecutor protagonista y los agentes internos de Contexia como capa de mejora/QA.

ANTES DE PROPONER NADA:
1. Lee HANDOFF-RENTA-NATURAL-2026.md (este archivo) completo.
2. Lee el canon que ya se auto-carga: CLAUDE.md, ARCHITECTURE.md, HARNESS.md.
3. Lee .antigravity/GROUND_TRUTH.md (manda en identidad/límites legales).
4. Verifica el estado real contra el código y Supabase — NO confíes en lo que digan los
   documentos de planeación sin comprobarlo (ver §6, "Lecciones aprendidas").

LUEGO:
- Entra en plan mode y propón el árbol de OpenSpec changes (no un solo change gigante).
- Respeta el flujo del repo: propose -> design -> spec -> tasks -> apply -> Stage 11 deploy
  -> archive. Un change a la vez.
- Usa el harness: leader -> implementer -> reviewer (HARNESS.md).

NO empieces a codificar hasta que yo apruebe el plan.
```

---

## 2. Convenciones del repo que se deben conservar (no negociables)

| Convención | Dónde vive | Regla |
|---|---|---|
| **OpenSpec** | `openspec/changes/<id>/` | Documentación es la fuente de verdad. Nada de código sin artefactos primero. Un change activo a la vez. |
| **Stage 11 obligatorio** | `DEPLOYMENT_STAGE/` | Un change no está "listo" hasta estar en producción + reporte de deployment. Nunca archivar sin desplegar. |
| **Harness de subagentes** | `.claude/agents/` | `leader.md` (planifica, no edita código) → `implementer.md` (UNA tarea, TDD) → `reviewer.md` (valida, no edita). Escriben a `progress/`, no al chat. |
| **TDD** | Global (CLAUDE.md §1) | Tests que fallan primero, siempre. |
| **Inglés en artefactos técnicos** | CLAUDE.md §2 | Código, config, docs técnicos = inglés. Excepción: resúmenes para el fundador pueden ser bilingües. |
| **`app/` es artefacto de build** | CLAUDE.md §9 | Nunca editar a mano. Fuente = `contexia-app/`. Bump `sw.js` CACHE_VERSION en cada deploy. |
| **Nunca fabricar stubs/mocks** | CLAUDE.md §9 | Si falta un archivo → investigar (git history), nunca inventar. Nunca desactivar type-checking. |
| **HITL siempre** | ARCHITECTURE.md | "Nous Never Approves" — Hermes/Manus jamás auto-aprueban una acción con efecto externo. |

### ⚠️ Conflicto a resolver antes de arrancar
CLAUDE.md §5 exige **Opus high reasoning** para workflows de planeación (`openspec-propose`,
`openspec-ff-change`, `openspec-continue-change`). Tú mencionaste querer planear en Fable y luego
Sonnet. **Decide explícitamente**: o (a) se respeta §5 y se planea en Opus, o (b) se actualiza §5
para permitir otro modelo. No lo dejes implícito — el agente del hilo nuevo va a intentar
auto-corregir el modelo según esa regla.

---

## 3. Skills recomendadas (por fase)

### Planeación (arranque del hilo)
- **`opsx:propose`** (o `openspec-propose`) — crea el change y genera proposal/design/tasks.
- **`opsx:explore`** — si quieres pensar en voz alta antes de comprometerte a un change.
- **`contexia-context`** — carga el contexto del ecosistema Contexia.
- **`anthropic-skills:contexia-ground-truth`** — identidad corporativa, Entidad A vs B, límites
  legales. **Crítico** para cualquier copy de la campaña (no prometer resultados fiscales).
- **`anthropic-skills:contexia-router`** — si dudas de qué skill/proyecto usar.

### Ejecución
- **`opsx:apply`** — trabaja `tasks.md` de arriba a abajo.
- **`using-git-worktrees`** — aísla el trabajo si vas a tocar varias áreas.
- **`commit`** — commits siguiendo el estándar del repo.

### Contenido / campaña
- **`anthropic-skills:contabilidad-colombia`** — precisión fiscal colombiana.
- **`anthropic-skills:contexia-ventas-clientes`** — el ángulo comercial.
- **`brand-voice:enforce-voice`** — aplica el manual de marca al copy (reemplaza/complementa al
  Content Critic interno).
- **`marketing:campaign-plan`** — estructura de campaña, calendario, métricas.
- **`marketing:draft-content`** — piezas por canal.
- **`anthropic-skills:canvas-design`** — si generas creatives.

### Cierre
- **`adversarial-review`** — revisión adversarial antes de archivar (el reviewer del harness la reusa).
- **`update-docs`** — actualiza ARCHITECTURE.md/AGENTES.md si cambian contenedores o agentes.
- **`opsx:archive`** — sincroniza specs y archiva.
- **`/code-review`** — revisión del diff antes de mergear.

---

## 4. MCP / plugins relevantes y su estado

| Servicio | Estado hoy | Para qué sirve aquí |
|---|---|---|
| **Supabase MCP** | ✅ Conectado | Migraciones, verificación de datos reales, RLS. **Úsalo para verificar, no confíes en docs.** |
| **Railway MCP** | ✅ Conectado | Deploy backend, env vars, logs. Ojo: cambiar una env var **no** dispara redeploy — hay que forzarlo. |
| **Vercel MCP** | ✅ Conectado | Deploy frontend, logs de build. |
| **HubSpot MCP** (`plugin:customer-support:hubspot`) | ⚠️ **Requiere autorización** | Si se decide usar HubSpot. Debes autorizarlo tú desde connector settings de claude.ai o `/mcp` en sesión interactiva. |
| **Canva MCP** (`plugin:marketing:canva`) | ⚠️ **Requiere autorización** | Generación de creatives. Tu memoria dice: siempre generar → crear → exportar PNG vía Canva MCP. |
| **GBrain MCP** | ✅ Conectado (intermitente) | Segundo cerebro. Vive en repo hermano `contexia-brain`, no aquí. |
| **Chrome / Browser** | ✅ | Verificación E2E visual en producción (obligatorio antes de declarar "listo"). |

**Nota sobre desconexiones:** los MCP de Supabase/Railway/GBrain se han desconectado y reconectado
varias veces en sesiones largas. Si un tool no aparece, usa `ToolSearch` antes de declarar que no
existe.

---

## 5. Estado REAL verificado (no lo que dicen los docs de planeación)

### ✅ Construido y en producción
- **CRM B2B**: `b2b_clients` (11 clientes) + `b2b_payments` (ene–jun 2026, cifras reales).
  Flag `CRM_CANONICAL=true`.
- **CRM B2C**: `crm_leads`, `crm_tax_profiles`, `crm_wompi_transactions` + Kanban de 4 etapas.
- **Sell Machine**: Copywriter + Content Critic + campaign_package → Approval Queue.
  Flag `SELL_MACHINE_CANONICAL=true`.
- **Puente Hermes↔Manus**: tabla `operator_tasks` con `task_type` genérico
  (`post_content`, `run_ads_ab`, `research`, `metrics_pull`, `external_integration`, `generate_doc`).
  Endpoints `/api/v1/sell-machine/tasks/*`.
- **Taty en WhatsApp**: Chatwoot (inbox 1, Channel::Whatsapp) → bridge → `TatyAgentService`.
  Un solo cerebro para WhatsApp/Telegram/PWA. Flag `WHATSAPP_CANONICAL=true`.
- **Wompi**: webhook real + HITL gate para links de pago.
- **Auth**: `AUTH_ENFORCED=true` en producción. Login único en `/login.html` (Google + email).
- **Social Content Ops 6a–6d**: generador de ideas, drafter de respuestas, cierre de ventas,
  analizador de métricas. Flag `SOCIAL_OPS_CANONICAL=true`.
- **Constantes fiscales**: corregidas 2026-08-12 (commit `8de4dad`) — UVT 2025 = $49.799,
  UVT 2026 = $52.374, umbral renta = $69.718.600, patrimonio = $224.095.500.

### ❌ NO construido / pendiente
- **Hermes NO está haciendo polling en producción.** Verificado: cero requests a
  `/sell-machine/tasks/pending` en logs de Railway; una tarea `pending` lleva >1 día sin reclamar.
  **Este es el bloqueador #1** — sin esto, nada de Manus se dispara automáticamente.
- **Ningún cliente B2B tiene login.** Los 11 tienen `login_user_id = NULL`,
  `provision_status = 'not_provisioned'`. Migración `0029_provision_client_users.sql` existe
  **pero no se ha corrido** (y crea cuentas vía SQL crudo — decisión tuya si se corre así o vía
  Supabase Admin API).
- **Feeding system del Búnker**: la pestaña B2B es solo-lectura. No hay alta/baja/pago desde la UI
  (change `per-tenant-client-access`, Stage 7, sin empezar).
- **Loop de retención**: no existe. Nadie detecta churn ni uso decreciente.
- **`user_tenants` / `user_roles`**: tablas **vacías**. El control de acceso corre 100% por el
  claim `role` del JWT de Supabase.
- **Túnel Cloudflare nombrado**: solo hay quick-tunnel efímero. Requiere que TÚ corras
  `cloudflared tunnel login` (OAuth interactivo).
- **`wompi-production-go-live`**: bloqueado esperando que hagas un pago real de producción.

### Usuarios reales hoy (4)
| Email | Rol | Uso |
|---|---|---|
| `contexia.marketing@gmail.com` | admin | Búnker |
| `jpelaezcardenas@gmail.com` | admin | Búnker (Google) |
| `growth@contexia.online` | cliente | PWA Cliente Cero |
| `fperez@ferez.co` | cliente | nunca se ha conectado |

---

## 6. Lecciones aprendidas (evitar repetirlas)

1. **Manus reporta cambios que NO llegan al repo.** Dijo haber corregido `constants.py`; el repo
   seguía con el valor viejo. Sus 3 proyectos (Strategy/Operations/Content Studio) viven en SU
   workspace. **Cualquier cambio de código debe entrar por git a este repo.** Manus puede proponer,
   no puede ser la fuente de verdad del código.
2. **Manus propuso operar SIN gate HITL** ("sin gate de aprobación en Bunker"). Esto contradice
   ARCHITECTURE.md. El "1 clic" que promete Manus debe SER la aprobación del Approval Queue, no un
   proceso paralelo.
3. **Verificar contra la realidad, no contra los docs.** Varios `tasks.md` decían 0% cuando estaba
   hecho, y viceversa. Consulta Supabase/logs/código directamente.
4. **Railway no redespliega al cambiar una env var.** Hay que forzar el redeploy.
5. **Nunca crear cuentas ni manejar credenciales por el agente.** Passwords, API keys, OAuth
   secrets, tokens: siempre los pone el fundador desde el dashboard correspondiente.

---

## 7. El diseño acordado (a formalizar en el hilo nuevo)

Manus protagonista en producción de contenido, agentes internos como capa de mejora,
loop de orquestación intacto, un solo HITL:

```
MANUS (produce)
  investiga tendencias + genera hooks/copy/creative
  + verifica claims contra Claim Ledger y UVT correcta
        ↓
AGENTES INTERNOS (mejoran — ya no generan desde cero)
  Copywriter → refina lo de Manus
  Content Critic → juzga contra marca/UVT/jerga opaca; fuerza reescritura
        ↓
campaign_package → Approval Queue (Supabase)
        ↓
TÚ: un solo clic en el Búnker (ESTE es el HITL real)
        ↓
operator_tasks (post_content / run_ads_ab)
        ↓
HERMES (local) hace polling → despacha a Manus
        ↓
MANUS ejecuta en Meta/FB/IG + A/B testing
        ↓
telemetría de vuelta → alimenta el prompt del próximo sprint (loop de 3 días)
```

**Invariantes**: nadie es protagonista único; el loop se auto-mejora con telemetría; toda acción
con efecto externo (publicar/gastar) pasa por el gate; Manus nunca toca datos financieros ni
conversa con clientes (eso es Taty).

---

## 8. Árbol de changes sugerido (a validar en plan mode)

Uno a la vez, en este orden. **No** un solo change gigante.

| # | Change | Desbloquea | Depende de |
|---|---|---|---|
| **1** | `hermes-polling-activation` | Que Manus se dispare automáticamente. **Bloqueador #1.** | Config local de Hermes (tú) |
| **2** | `manus-first-creative-pipeline` | Invertir el orden: Manus produce, agentes internos mejoran | #1 |
| **3** | `bunker-crm-feeding-system` | Alta/baja/pago de clientes desde el Búnker sin tocar Supabase | — (independiente) |
| **4** | `client-login-provisioning` | Que los 11 clientes B2B entren a su propia PWA | #3 (o independiente) |
| **5** | `retention-loop` | Detección de churn + acciones de retención | #1, #2 |
| **6** | `crm-hubspot-sync` *(opcional)* | Vista comercial en HubSpot | Autorizar HubSpot MCP |

**Decisión pendiente tuya antes del #6**: HubSpot free (1 solo pipeline, 1.000 contactos) vs
Chatwoot self-hosted vs seguir 100% en Supabase. Ya se investigó — Evo CRM Community (brasileño,
Evolution Foundation) se descartó por ser v1.0 muy joven y depender de WhatsApp no-oficial
(riesgo de bloqueo de número), inconsistente con el Cloud API oficial que ya usa Taty.

---

## 9. Decisiones que solo tú puedes tomar (bloquean partes del plan)

- [ ] ¿Se respeta CLAUDE.md §5 (planear en Opus) o se actualiza la regla?
- [ ] ¿HubSpot, Chatwoot, o solo Supabase? (§8 #6)
- [ ] ¿Se corre la migración `0029` con SQL crudo, o se reescribe usando Supabase Admin API?
- [ ] Autorizar HubSpot MCP y/o Canva MCP (desde claude.ai connector settings o `/mcp`).
- [ ] Correr `cloudflared tunnel login` + `tunnel create` para el túnel nombrado.
- [ ] Hacer el pago real de producción que desbloquea `wompi-production-go-live`.
- [ ] Definir tarifas de Renta Natural (hoy el system prompt de Taty tiene prohibido inventar precio).
- [ ] Primer segmento de la campaña: ¿asalariados o informales/Nequi?
