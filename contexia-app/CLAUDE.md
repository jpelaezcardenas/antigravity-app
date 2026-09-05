# Contexia App — Guía para Claude

Demo mock visual de la app Contexia. Stack: Next.js 16 App Router + React 19 + TypeScript estricto + Tailwind v4 (PostCSS-only, tokens en `@theme`).

## Reglas duras

- **Sin backend, sin fetch, sin auth, sin DB**, **EXCEPTO**: pantallas data-bound (Pulso/Overview → Caja Real, Alertas Activas; Flujo-detalle → Puente de Liquidez; Búnker → Social Content Ops; Búnker → Onboarding; Búnker → CRM/Ventas; Búnker → Sell Machine; Config → identidad/plan del tenant; el banner "actualiza tu plan" en Fiscal/Radar/Patrimonio; Radar → Radar de Caja 13 Semanas) PUEDEN hacer fetch al backend Contexia (`/api/v1/*`), incluyendo escrituras cuando esa pantalla lo requiere (Caja Real, Alertas Activas, Puente de Liquidez, Config, el banner de upgrade y Radar de Caja 13 Semanas son solo lectura; Social Content Ops, Onboarding, CRM/Ventas B2C, y Sell Machine escriben; CRM/Ventas B2B es de solo lectura — ver abajo). Ver [Pantallas data-bound](#pantallas-data-bound). Todo lo demás sigue siendo mock local tipado en `lib/mock/`.
- **Regla dura — nunca mock como fallback de error**: ninguna pantalla data-bound puede, ante un fetch fallido, mostrar datos de `lib/mock/*` presentados como si fueran reales. El estado de error debe ser explícito y honesto (discreto, sin banner alarmante) — nunca datos inventados bajo un estado "ready"/"listo". Incidente que originó esta regla: `CashTodayCard` caía silenciosamente a `pulsoMock.cash` en error, marcado como `"ready"` — corregido en `pwa-tenant-aware-screens` (ver abajo).
- **Fuente de verdad visual**: el export de Stitch y los screenshots `screen.png` del ZIP `stitch_contexia_evolution_cfo_as_a_service`. No rediseñar pantallas que Stitch ya definió.
- **Sin CDN**: nada de React/Tailwind/Babel por unpkg. Las únicas URLs externas son Google Fonts (Inter, JetBrains Mono, Material Symbols) cargadas desde [app/layout.tsx](app/layout.tsx).
- **Sin librerías nuevas** salvo que sea estrictamente necesario. Stack mínimo.
- **Tokens**: usar las clases generadas por `@theme` en [app/globals.css](app/globals.css) (`bg-surface-elevated`, `text-primary-container`, `px-container-margin-mobile`, etc.). No introducir colores ad-hoc.
- **UTF-8 limpio**: sin mojibake ("operación" no "operaciÃ³n").

## Pantallas data-bound

`CashTodayCard` (Pulso/Overview) es la primera pantalla data-bound (de 7 hoy).
Es un `"use client"` componente que se autoabastece (no recibe props de datos):
`useEffect` + `fetchFinancials()` (`lib/api-client.ts`) en mount, con estados
`loading` / `error` / `empty` / `ready` explícitos en el render — nunca queda en
blanco ni revienta si el backend no responde.

- **API config**: `lib/config.ts` expone `API_BASE_URL` (default: Railway prod)
  y `API_ENDPOINTS`.
- **Cliente tipado**: `lib/api-client.ts` (`fetchFinancials()` + `FinancialsSnapshot`).
- **Granularidad diaria — promesa de venta**: el backend (`GET /api/v1/financials`)
  devuelve `caja_real` (balance acumulado a hoy), `ventas_ayer`/`gastos_ayer`
  (exclusivamente el día anterior, NO un agregado mensual). No relabelees datos
  mensuales como "de ayer" — si el backend no tiene la granularidad que el
  componente promete, hay que arreglar el backend, no el texto.
- **Unidades**: el backend devuelve COP en centavos (minor units); `formatCop`
  espera COP completos — dividir entre 100 al mapear la respuesta.
- **Mocks**: el resto de cards de Pulso (Health, Note) siguen en mocks (Alerts
  pasó a data-bound, ver abajo), igual que Fiscal, Radar, Patrimonio, y el resto
  de cards de Flujo-detalle (solo el Puente de Liquidez es data-bound).

### Pulso/Overview → Alertas Activas (segunda excepción data-bound, `pwa-tenant-aware-screens`)

`ActiveAlerts` (Pulso/Overview) sigue el mismo patrón self-feeding que
`CashTodayCard`: `"use client"` + `useEffect` + `fetchCentinelaAlerts()`
(`lib/api-client.ts`) en mount, sin prop `alerts`. Estados: `loading` (skeleton)
/ `ready` (alertas reales) / vacío-o-error → no renderiza nada (misma sección
oculta que ya existía cuando `alerts.length === 0`) — nunca cae a
`pulsoMock.alerts`.

- **Backend**: `GET /api/v1/centinela/alerts` (nuevo, distinto del legado
  `GET /centinela/alerts/{company_id}` que sigue usando Hermes) — tenant-scoped,
  sin demo fallback.
- **Claves de React**: el backend puede devolver múltiples alertas con el mismo
  `rule_id` (una regla dispara una vez por documento afectado — confirmado en
  vivo con 20 alertas reales compartiendo `SHADOW_GL_DISCREPANCY`). La key
  SIEMPRE debe incluir el índice del array (`` `${rule_id}-${index}` ``) — nunca
  asumir que un campo del backend es único sin verificarlo contra datos reales.

### Flujo-detalle → Puente de Liquidez (tercera excepción data-bound, `pwa-tenant-aware-screens`)

`MonthlyLiquidityBridgeCard` (Flujo-detalle) es self-feeding igual que las
anteriores: `fetchLiquidityBridge()` (`lib/api-client.ts`). Estados: `loading`
/ `ready` (÷100 → `formatCop`) / `unavailable` (fetch falla o `status: "empty"`)
→ "Datos no disponibles por el momento.", nunca `flujoDetalleMock.liquidityBridge`.
La página (`app/flujo-detalle/page.tsx`) sigue siendo Server Component — solo
la card es cliente; las otras tres cards de la pantalla (`FlowCompositionCard`,
`FinancialHealthStatusGrid`, `StructuralInsightCard`) siguen en mock — el Shadow
GL no tiene la clasificación (operación/inversión/financiación) que esas cards
prometen.

- **Backend**: `GET /api/v1/financials/liquidity-bridge` (nuevo), mismo
  resolver de tenant que `/financials`. `final_balance` coincide exactamente
  con `caja_real` de `/financials` para el último día del mes — verificado en
  tests y en vivo.

### Búnker → Social Content Ops (cuarta excepción data-bound)

`components/bunker/social-ops/SocialContentOpsSection.tsx` (+ `IdeasTab`,
`CalendarioTab`, `BorradoresTab`, `MetricasTab`) es la cuarta pantalla
data-bound. A diferencia de `CashTodayCard` (solo lectura), esta sí escribe:
crea eventos, diagnostica leads, genera borradores IA, aprueba/rechaza
(HITL). Backend real ya desplegado (`apps/backend/presentation/
social_ops_endpoints.py`, gateado por el feature flag `SOCIAL_OPS_CANONICAL`,
`true` en Railway `-175a` desde 2026-07-15 — reemplaza n8n como handler de
Social Ops en producción).

- **Cliente tipado**: `lib/social-ops-api.ts`.
- **Ideas / Métricas / Calendario / Borradores** completan el pipeline
  Ideas → Calendario → Borradores → Métricas que `AGENTES.md` documenta como
  "preservado" (Tier 3, agentes 6a–6d). Calendario/Borradores son endpoints
  nuevos (mismo patrón Supabase-preferido/demo-fallback que ideas/metrics) —
  antes vivían solo en un dashboard Vite no enlazado, contra un proyecto
  Supabase distinto y no documentado (el sandbox del Wizard).
- **HITL intacto**: todo borrador queda en `pending_approval`; el tab
  Aprobaciones es el único gate que libera una acción outbound.

### Búnker → Onboarding (quinta excepción data-bound)

`components/bunker/onboarding/OnboardingSection.tsx` es la quinta pantalla
data-bound, mismo backend canónico que Social Content Ops (`SOCIAL_OPS_CANONICAL`,
ya activo). Igual que Social Content Ops, escribe (inicia onboarding, envía intake,
crea seed drafts), no es solo lectura.

- **Cliente tipado**: mismas funciones de `lib/social-ops-api.ts` (extendido con
  las de onboarding: `getSocialOpsOnboarding`, `startSocialOpsOnboarding`,
  `advanceSocialOpsOnboardingStep`, `createSocialOpsOnboardingSeed`,
  `intakeSocialOpsOnboarding`).
- **Flujo**: formulario de inicio (empresa/email/pago/plan/owner) → selector de
  workspace con SLA/QA targets → intake en lenguaje natural (IA extrae
  credenciales presentes/faltantes) → seed draft → checklist de 21 días
  (S1/S2/S3 + Go-Live).
- **HITL intacto**: seed drafts quedan en `pending_approval`, igual que el resto.

### Búnker → CRM/Ventas B2B + B2C (sexta excepción data-bound)

`components/bunker/CrmVentasSection.tsx` (tab shell) is the sixth data-bound screen, with two
live tabs sharing the same backend (`apps/backend/presentation/crm_endpoints.py`, gated by
`CRM_CANONICAL` — default `false`, activated after the production smoke-test, same playbook as
`SOCIAL_OPS_CANONICAL`):

- **"B2B / Retainers"** (`components/bunker/crm/B2bRetainersTab.tsx`) — **reads and writes**
  (per-tenant-client-access, Phase B): the real roster of Contexia's B2B retainer clients (monthly
  retainers, formerly a manual Excel) and the Jan–Jun payment grid, sourced from Supabase. Was
  read-only through `crm-b2b-retainers-cockpit`; now the founder + accountant feed the roster
  directly from this tab — alta (new client, own tenant + best-effort login provisioning), baja/
  reactivar (toggle the status badge), and pago (click a grid cell to record/correct one month).
- **"B2C / Renta Natural"** (`components/bunker/crm/B2cKanbanTab.tsx`) — **reads and writes**, like
  Social Content Ops: a 4-stage Kanban funnel (Nuevos → Prospectos → Por Aprobar → Listos
  Contadora) for the Renta Natural 2026 lead pipeline. Writes: advancing a lead's stage, and the
  "Aprobar Pago" HITL action (only on `POR_APROBAR` cards), which advances the lead to
  `LISTOS_CONTADORA` and stamps its associated Wompi transaction row `APPROVED`. Payment
  verification itself is seeded/simulated only in this change (`crm-b2c-sell-machine-cockpit`) —
  no live Wompi integration yet.

- **Cliente tipado**: `lib/crm-api.ts` (both tabs share this client).
- **Patrón**: idéntico al de `IdeasTab.tsx` — `useEffect` + `useState` con estados `loading`/
  `error`/`source` explícitos, tokens `@theme` únicamente, sin librerías nuevas, sin
  drag-and-drop (click-to-advance en vez de arrastrar).
- **Unidades**: el backend devuelve `amount_cents` (COP en centavos); dividir entre 100 con
  `formatCop` al renderizar, igual que Caja Real.

### Búnker → Sell Machine (séptima excepción data-bound)

`components/bunker/sell-machine/SellMachineSection.tsx` es la séptima pantalla data-bound, gateada
por `SELL_MACHINE_CANONICAL` (mismo playbook que `SOCIAL_OPS_CANONICAL`/`CRM_CANONICAL`). Es el
loop creativo del Sell Machine: un agente Copywriter genera hooks de marketing, un agente Content
Critic (evaluator-optimizer) los filtra contra la marca de Contexia (nunca framear a Contexia como
firma contable regulada, evitar tono robótico/jerga opaca), y los sobrevivientes se empaquetan como
un `campaign_package` que entra al **Approval Queue existente de Supabase** (no una tabla nueva) —
Juan David aprueba/rechaza desde el Búnker antes de que cualquier cosa se publique en cualquier
lado. Esta pantalla **no publica nada** — solo produce un registro aprobado; la ejecución real
(Meta/Manus) es un change futuro (F).

- **Cliente tipado**: `lib/sell-machine-api.ts`. El approve/reject reutiliza los endpoints
  genéricos ya existentes `/api/v1/approval-queue/approve` y `/reject` (no son específicos de
  Sell Machine — no se tocó ese código).
- **Escribe**: generar hooks, evaluar hooks, crear campaign package, aprobar/rechazar (vía la
  Approval Queue). Igual que Social Content Ops y CRM/Ventas B2C.
- **HITL**: todo campaign package queda `pending_approval` en la Approval Queue; no hay ninguna
  ejecución automática — Juan David es el único gate.

### Config → identidad/plan del tenant + banner "actualiza tu plan" (octava excepción data-bound, `plan-tier-feature-gating`)

`components/config/TenantInfoCard.tsx` reemplaza el bloque hardcodeado
`"Mi Empresa" / "Plan Starter · Activo"` de `app/app/(shell)/config/page.tsx` —
self-feeding igual que las anteriores: `fetchTenantMe()` (`lib/api-client.ts`) en
mount, estados `loading` (skeleton) / `ready` (nombre + tier reales) / `empty`
(placeholder neutral "Mi Empresa" / "Plan", nunca un banner de error — la
identidad del tenant no es un dato crítico que amerite alarmar). Solo lectura.

`components/shared/UpgradePlanBanner.tsx` es un componente compartido, montado
en Fiscal, Radar y Patrimonio — llama al mismo
`fetchTenantMe()` y solo se renderiza (una línea "Actualiza tu plan para
desbloquear esta función") cuando `plan_tier === "freemium"`; en cualquier otro
caso (loading, error, tier pagado) no renderiza nada, sin flash de layout.
Fiscal y Patrimonio siguen siendo 100% mock por lo demás — este banner es puramente
presentacional y no implica que la pantalla tenga datos reales. **Radar dejó de ser
100% mock** a partir de `radar-cash-projection-13w` (ver la novena excepción abajo):
su sección "Radar de Caja 13 Semanas" lee datos reales, mientras el resto de sus
cards (selector de escenario, proyección 30 días, provisión de impuestos, insight,
milestones) siguen en `lib/mock/radar.ts`.

- **Backend**: `GET /api/v1/tenant/me` (nuevo), resuelto vía el resolver
  canónico `resolve_request_tenant_scope` (a diferencia de `/financials`, que
  mantiene su resolver local por razones históricas — ver
  `openspec/changes/plan-tier-feature-gating/design.md` D5).
- **`CashTodayCard`, `ActiveAlerts`, `MonthlyLiquidityBridgeCard`** ganaron un
  estado adicional (`not_in_plan` en dos de los tres — `CashTodayCard` nunca lo
  alcanza porque `pulso_diario` está incluido en todos los tiers, incluido
  freemium) — ver `design.md` D3/D4 para el razonamiento completo por
  componente.

### Búnker → Dashboard · Métricas Operacionales (novena excepción data-bound, `metrics-dashboard-phase9`)

`components/bunker/metrics/MetricsDashboardSection.tsx` ensambla 4 tarjetas self-feeding en la
sección Dashboard del Búnker (debajo de `InfrastructureDashboard`):

- **`AutoApprovalCard`** — `GET /api/v1/metrics/auto-approval/last-7-days`: total auto-aprobado,
  desglose por regla (recurrentes/vendor/micro), tasa de falsos positivos, mini bar chart de los
  últimos 7 días.
- **`QueueHealthCard`** — `GET /api/v1/metrics/queue-health`: pendientes en cola + tiempo promedio
  de revisión. Cambia color según urgencia (verde/amarillo/rojo).
- **`CSVIngestionCard`** — `GET /api/v1/metrics/csv-ingestion/last-7-days`: archivos procesados,
  filas OK vs filas con error, tasa de error por día.
- **`TopVendorsCard`** — `GET /api/v1/metrics/top-vendors`: top 10 proveedores con bar chart
  proporcional al volumen de transacciones.

- **Cliente tipado**: `lib/metrics-client.ts` (`fetchAutoApprovalMetrics`, `fetchCSVIngestionMetrics`,
  `fetchQueueHealth`, `fetchTopVendors`).
- **Solo lectura** — no escribe al backend.
- **Estado vacío explícito**: si no hay snapshots en DB aún, cada tarjeta muestra
  "Sin datos disponibles" — nunca datos inventados.
- **Backend**: tabla `metrics_snapshots` (migración `0045`), `services/metrics_service.py`,
  `presentation/metrics_endpoints.py` registrado en `main.py`. RLS: cada tenant ve solo sus datos;
  el rol `service_role` escribe los snapshots nocturnos.

### Radar → Radar de Caja 13 Semanas (novena excepción data-bound, `radar-cash-projection-13w`)

`components/radar/CashProjection13wCard.tsx` es self-feeding igual que `CashTodayCard`:
`fetchCashProjection13w()` (`lib/api-client.ts`) en mount, **solo lectura**. Estados
explícitos: `loading` (skeleton) / `ready` (gráfico de 13 puntos + narrativa) /
`sin_historico_suficiente` (mensaje honesto "aún no tenemos suficiente historial") /
`tenant_no_resuelto` / `error` — nunca cae a `radarMock`.

- **Backend**: `GET /api/v1/radar/proyeccion-caja` (nuevo), tenant resuelto vía el
  resolver canónico `resolve_request_tenant_scope`, sin query param de tenant.
- **Metodología honesta**: la respuesta trae `metodologia: "solo_historico"` —
  no existen tablas de CxC/CxP con fecha de vencimiento en el modelo de datos, así
  que la proyección es extrapolación de tendencia, no un forecast con compromisos
  conocidos. `impuesto_futuro_estimado` viene siempre `null` (no hay cálculo real de
  impuesto en el backend). **No inventar ni mockear ese número en la UI.**
- **Confianza**: solo dos bandas, `"media"` (semanas 1-4) y `"baja"` (5-13). **Nunca
  existe `"alta"`** — colorear con dos colores, no tres.
- **Gráfico sin librerías**: SVG inline (`viewBox="0 0 100 100"` + `path d`), misma
  técnica que `CashProjectionCard.tsx` ya usaba. Se evaluó Recharts y se descartó por
  la regla dura "no agregar dependencias sin razón fuerte" — ver
  `openspec/changes/radar-cash-projection-13w/design.md` Decisión #6.
- **Sin tracking**: el evento de adopción del brief original quedó fuera de alcance —
  no existe infraestructura de analytics en `contexia-app` a la cual engancharse.

Esto es una excepción escoped al charter "sin backend" — pantallas data-bound son
un puente hacia el MVP data-driven; mocks aplican para todo lo demás.

### Fetch autenticado (bunker-pwa-auth-enforcement)

El login real de la PWA/Búnker **ya existía antes de este change** y no vive en `contexia-app`:
`login.html` (raíz del repo) autentica contra **Supabase Auth**
(`client.auth.signInWithPassword`), guarda el access token en `localStorage["token"]` y una cookie
`sb-access-token`, y `middleware.ts` (Vercel Edge, raíz del repo) ya protege cada navegación a
`/app/*`/`/app-admin/*` verificando esa cookie server-side — incluyendo el gate por rol
(`/app/bunker` requiere `app_metadata.role=admin`). Ninguno de los dos se toca desde
`contexia-app`.

Lo que sí faltaba (al momento de `bunker-pwa-auth-enforcement`): las pantallas data-bound llaman
al backend en Railway **directamente** (bypaseando el dominio de Vercel y por lo tanto
`middleware.ts`), sin adjuntar nunca ese token. `lib/authenticated-fetch.ts` cierra ese hueco —
adjunta `Authorization: Bearer` leyendo el mismo `localStorage["token"]` que `login.html` ya
llena, usado internamente por todos los clientes tipados de arriba (`api-client.ts`,
`social-ops-api.ts`, `crm-api.ts`, `sell-machine-api.ts` — sus firmas exportadas no cambian
cuando se agregan nuevas funciones). Es deliberadamente mínimo: no redirige ni limpia sesión en
un 401 — eso ya lo hace `middleware.ts` del lado servidor, más robusto que cualquier cosa que
este helper pudiera duplicar del lado cliente.

## Reglas de interactividad (mock-first, pero viva)

La demo debe **sentirse real**. Estado local con `useState` siempre que un control cambie lo que el usuario ve.

**Sí:**
- Tabs / chips / toggles cambian el contenido visible (ej. Radar: pesimista/base/optimista).
- Inputs recalculan métricas, badges y mensajes con reglas locales simples (ej. Patrimonio simulator: `cajaConRetiro = cajaSinRetiro - amount`).
- Filtros, drawers, selects, sliders pueden modificar lo que se muestra.
- Las alertas y tarjetas pueden expandirse, colapsarse o navegar a vistas mock.
- Cualquier cambio de estado puede tocar métricas, mensajes, badges, colores y CTAs visibles.

**No:**
- Llamadas a backend o APIs reales.
- Cálculos financieros precisos contra datos externos.
- Persistencia (localStorage, cookies, DB).
- Auth ni roles reales.

**Patrón estándar — toggle con mocks por escenario:**

```tsx
// lib/mock/radar.ts
export const radarMock: Record<Scenario, RadarScenarioData> = {
  pesimista: { chartPathD: "M0,40 L20,55 ...", provision: { ... }, insight: "...", milestones: [...] },
  base:      { chartPathD: "M0,80 L20,60 ...", provision: { ... }, insight: "...", milestones: [...] },
  optimista: { chartPathD: "M0,90 L20,70 ...", provision: { ... }, insight: "...", milestones: [...] },
};

// app/app/radar/page.tsx
"use client";
import { useState } from "react";
const [scenario, setScenario] = useState<Scenario>("base");
const data = radarMock[scenario];
// pasar data.* a cada sub-componente
```

**Patrón estándar — input con cálculo local:**

```tsx
// components/patrimonio/WithdrawalSimulator.tsx
"use client";
import { useState } from "react";
const [amount, setAmount] = useState(defaultAmount);
const cajaConRetiro = cajaSinRetiro - amount;
const ratio = amount / cajaSinRetiro;
const status: StatusLevel = ratio > 0.3 ? "alerta" : ratio > 0.15 ? "vigilancia" : "sana";
```

Las reglas para derivar `status`/mensajes/colores viven en cada componente o en helpers de `lib/`. No hay que pedir lógica financiera "real" — la regla simple que se sienta plausible es suficiente.

## Arquitectura

- **Pantallas tab principal**: `app/app/<ruta>/page.tsx` bajo el route group `app/app/` que tiene shell con TopBar + BottomNav + FAB.
- **Pantallas detalle** (sin BottomNav, con back button): viven fuera del route group, ej. `app/flujo-detalle/page.tsx` con su propio `layout.tsx`.
- **Server Components por defecto.** Marcar `"use client"` solo cuando se usa estado, eventos o `next/navigation` hooks.
- **Mocks**: un archivo por pantalla en `lib/mock/`. Tipos en `lib/types/contexia.ts`.
- **Componentes UI**: agrupados por pantalla en `components/<pantalla>/`. Compartidos van a `components/layout/` o `components/ui/` si surge la necesidad.

## Convenciones de naming

- Tabs del BottomNav: Pulso (`/app/overview`), Fiscal (`/app/fiscal`), Radar (`/app/radar`), Config (`/app/config`).
- Pantallas detalle: `/app/<nombre-detalle>` (ej. `/app/flujo-detalle`, `/app/patrimonio`).
- Componentes: PascalCase. Archivos: PascalCase para componentes, kebab-case o camelCase para utilidades.
- Tipos del dominio: en [lib/types/contexia.ts](lib/types/contexia.ts).
- Mocks: `pulsoMock`, `radarMock`, `fiscalMock`, etc. (camelCase, sufijo Mock).

## PWA (activa)

El registro de service worker es código activo, no un slot inerte:
- `public/sw.js` → copiado al export como `sw.js` (servido en `/sw.js`, scope raíz).
- `app/layout.tsx` renderiza `<RegisterSW />` (`app/register-sw.tsx`) incondicionalmente, que llama
  `registerServiceWorker()` (`lib/sw-register.ts`) en mount: `navigator.serviceWorker.register("/sw.js", { scope: "/" })`.
- `app/manifest.ts` (Next 16 metadata route) genera el manifest.
- `public/icons/` para iconos PWA.

**Regla dura — versionado obligatorio**: `public/sw.js` cachea bajo `CACHE_NAME = contexia-${CACHE_VERSION}`.
**`CACHE_VERSION` debe bumpearse en cada build que cambie assets cacheados** (HTML shell o `/_next/static/`
patterns). Un `CACHE_VERSION` fijo entre deploys causa que el SW sirva HTML/chunks viejos indefinidamente — esto
ya causó un incidente de producción (ver `antigravity-app/CLAUDE.md` sección 9). El SW usa network-first para
navegación/HTML y cache-first para assets estáticos, lo cual mitiga pero no reemplaza el bump de versión.

## No hacer

- No tocar `contexia-wizard/` (proyecto hermano, captación de leads — separado).
- No unificar tokens con `--ctx-*` del wizard. Los design systems viven separados.
- No crear pantallas que no estén en el export de Stitch sin pedido explícito.
- No agregar dependencias sin razón fuerte (no zustand, no zod, no RHF, no librerías de UI).
