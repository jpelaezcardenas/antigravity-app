# Contexia App — Demo Mock

Demo mock visual de la app Contexia (Pulso Diario / Centinela Fiscal / Radar Predictivo / Patrimonio) construida sobre **Next.js 16 App Router + Tailwind v4 + TypeScript**. Esta primera iteración cubre la pantalla **Pulso** en `/app/overview`.

Sin backend, sin auth, sin APIs. Datos mock tipados en `lib/mock/`.

## Stack

- Next.js 16.2.4 (App Router) + React 19
- TypeScript estricto
- Tailwind CSS v4 (PostCSS-only, tokens en `@theme`)
- Fuentes Inter + JetBrains Mono + Material Symbols Outlined vía Google Fonts

## Arranque

```bash
cd contexia-app
npm install
npm run dev
```

Abrir http://localhost:3000 — redirige a `/app/overview`.

## Logo

Guardar el logo de Contexia (PNG, idealmente 256×256 o superior) en:

```
contexia-app/public/logo.png
```

El TopBar lo carga desde `/logo.png` (Next.js con `images.unoptimized: true`, así que se sirve tal cual).

## Estructura

```
app/
├── layout.tsx             # html lang=es, fonts, Material Symbols
├── globals.css            # @theme tokens Stitch + utilidades
├── page.tsx               # redirect → /app/overview
└── app/
    ├── layout.tsx         # Shell: TopBar + BottomNav + FAB
    └── overview/
        └── page.tsx       # Pulso Diario

components/
├── layout/
│   ├── TopBar.tsx         # Client (useRouter)
│   ├── BottomNav.tsx      # Client (usePathname)
│   └── FAB.tsx            # Server
└── pulso/
    ├── NoteOfDayCard.tsx
    ├── CashTodayCard.tsx
    ├── HealthQuadrant.tsx
    └── ActiveAlerts.tsx

lib/
├── types/contexia.ts      # Contratos del dominio (PulsoData, etc.)
├── mock/pulso.ts          # Datos mock de la pantalla Pulso
└── format.ts              # formatCop helper
```

## Próximas pantallas (no implementadas todavía)

Los tabs del BottomNav apuntan a:

- `/app/overview` ✅ (Pulso)
- `/app/fiscal` (Centinela Fiscal)
- `/app/radar` (Radar Predictivo)
- `/app/config` (Patrimonio / Config)

Se irán agregando como `app/app/<ruta>/page.tsx` siguiendo el mismo patrón.

## PWA (fase 2)

La arquitectura ya está lista para activar PWA sin tocar componentes:

- `app/manifest.ts` (metadata route de Next 16)
- `public/icons/` (iconos 192/512/maskable)
- Registro de service worker en `app/layout.tsx`
