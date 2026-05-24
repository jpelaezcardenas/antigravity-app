# Contexia App — Guía para Claude

Demo mock visual de la app Contexia. Stack: Next.js 16 App Router + React 19 + TypeScript estricto + Tailwind v4 (PostCSS-only, tokens en `@theme`).

## Reglas duras

- **Live + mock fallback** (cambio 2026-05-27, PHASE 2 DAY 3): Los componentes integrados con backend (Taty, Centinela, Radar) hacen `fetch` real a la API FastAPI vía el cliente en `lib/api/`. Si el backend falla (5xx, network error), caen al mock correspondiente en `lib/mock/` para no romper la demo. Componentes que aún no tienen endpoint backend siguen siendo mock-only.
- **API base URL**: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Toda llamada va por `lib/api/client.ts`.
- **Sin auth todavía**: el `company_id` se pasa como prop o se hardcodea (`ctx-001` por defecto) hasta que se conecte autenticación real.
- **Sin DB en frontend**: nada de localStorage para datos de negocio; sí permitido para preferencias UI mínimas (tema, último scenario seleccionado).
- **Fuente de verdad visual**: el export de Stitch y los screenshots `screen.png` del ZIP `stitch_contexia_evolution_cfo_as_a_service`. No rediseñar pantallas que Stitch ya definió.
- **Sin CDN**: nada de React/Tailwind/Babel por unpkg. Las únicas URLs externas son Google Fonts (Inter, JetBrains Mono, Material Symbols) cargadas desde [app/layout.tsx](app/layout.tsx).
- **Sin librerías nuevas** salvo que sea estrictamente necesario. Stack mínimo.
- **Tokens**: usar las clases generadas por `@theme` en [app/globals.css](app/globals.css) (`bg-surface-elevated`, `text-primary-container`, `px-container-margin-mobile`, etc.). No introducir colores ad-hoc.
- **UTF-8 limpio**: sin mojibake ("operación" no "operaciÃ³n").

## Reglas de interactividad (mock-first, pero viva)

La demo debe **sentirse real**. Estado local con `useState` siempre que un control cambie lo que el usuario ve.

**Sí:**
- Tabs / chips / toggles cambian el contenido visible (ej. Radar: pesimista/base/optimista).
- Inputs recalculan métricas, badges y mensajes con reglas locales simples (ej. Patrimonio simulator: `cajaConRetiro = cajaSinRetiro - amount`).
- Filtros, drawers, selects, sliders pueden modificar lo que se muestra.
- Las alertas y tarjetas pueden expandirse, colapsarse o navegar a vistas mock.
- Cualquier cambio de estado puede tocar métricas, mensajes, badges, colores y CTAs visibles.
- **Llamadas a backend reales** (Taty/Centinela/Radar y futuros endpoints): siempre con fallback al mock en caso de error.

**No:**
- Cálculos financieros precisos contra datos externos (los costos siguen siendo demos).
- Persistencia de datos de negocio en localStorage (sólo prefs UI mínimas).
- Auth ni roles reales (todavía — fase 3).

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

## PWA (fase 2, no iniciada)

Slots reservados pero inertes:
- `public/icons/` para iconos PWA
- `app/manifest.ts` (Next 16 metadata route) para el manifest
- Registro de service worker en `app/layout.tsx`

No tocar hasta que se active la fase PWA.

## No hacer

- No tocar `contexia-wizard/` (proyecto hermano, captación de leads — separado).
- No unificar tokens con `--ctx-*` del wizard. Los design systems viven separados.
- No crear pantallas que no estén en el export de Stitch sin pedido explícito.
- No agregar dependencias sin razón fuerte (no zustand, no zod, no RHF, no librerías de UI).
