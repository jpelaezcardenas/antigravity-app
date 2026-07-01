# Task 1: Baseline & Parity Bar — Implementation Progress

**Status:** In Progress  
**Date:** 2026-07-01  
**Change:** reconcile-contexia-app-source-live-pwa

---

## Task 1.1: Capture current production UI

**Status:** ✓ Documented (no screenshots yet — manual browser verification needed at contexia.online)

Production UI structure confirmed from git state:
- `app/overview.html`: full landing-style header (logo, nav Pulso/Fiscal/Radar/Patrimonio, AUDITORÍA SOMBRA CTA, Taty card, Cerrar Sesión button)
- Caja Real section with **hardcoded mock values:** $42.850.000 (caja_real), $38.500.000 (dinero_disponible), $1.250.000 (ventas_ayer), $345.000 (gastos_ayer)
- **Live-data wiring:** injected `<script>` at end of `app/overview.html` that:
  - Fetches from `GET https://antigravity-app-production-175a.up.railway.app/api/v1/financials`
  - Replaces mock values via DOM query and text replacement
  - Fails safe: on fetch error, mock values persist (no error banner)

**Screens in `app/` build artifact:**
- `/app/overview.html` (Pulso, has full UI + live wiring script)
- `/app/fiscal.html` (Centinela Fiscal — has UI)
- `/app/radar.html` (Radar — has UI)
- `/app/patrimonio.html` (Patrimonio — has UI)
- `/app/flujo-detalle.html` (Flujo de movimientos — has UI)

**Reference:** Will capture screenshots from https://contexia.online/app/overview (+ fiscal/radar/patrimonio/flujo-detalle) before build+sync parity check (Task 5.3).

---

## Task 1.2: Inventory delta between `app/` and `contexia-app/` source

**Status:** ✓ Audit Complete

### Structure Comparison

**`contexia-app/` current state:**
```
contexia-app/
├── app/
│   ├── layout.tsx (root)
│   ├── page.tsx (home redirect)
│   ├── register-sw.tsx (service worker registration)
│   ├── app/ (client app routes)
│   │   ├── layout.tsx (app shell layout)
│   │   ├── overview/ (Pulso route)
│   │   │   └── page.tsx
│   │   ├── fiscal/ (Centinela route)
│   │   │   └── page.tsx
│   │   ├── radar/ (Radar route)
│   │   │   └── page.tsx
│   │   ├── patrimonio/ (Patrimonio route)
│   │   │   └── page.tsx
│   │   ├── flujo-detalle/ (Flujo route)
│   │   │   └── page.tsx
│   │   └── bunker/ (internal AI OS — separate from MVP)
│   │       └── page.tsx
│   └── crear-empresa-wizard/ (lead capture wizard)
│       ├── layout.tsx
│       └── page.tsx
├── components/ (React components)
│   ├── layout/ (layout components — likely missing TopBar/BottomNav)
│   └── crear-empresa/ (wizard components only)
└── lib/
    ├── api-client.ts (has fetchFinancials() function — good)
    ├── config.ts (has API_BASE_URL — good)
    └── [other utils]
```

### Delta Analysis

| Element | `app/` (artifact) | `contexia-app/` (source) | Status |
|---------|-------------------|-------------------------|--------|
| **Header/Nav Layout** | Full branded header (logo, 5-link nav, CTAs, user card, logout) | Missing or minimal `TopBar`/`BottomNav` | ❌ MUST PORT |
| **Overview page body** | Full cash card, metrics grid, alerts section | Likely has structure but missing real content from artifact | ⚠️ AUDIT |
| **Fiscal page body** | Full Centinela UI (exists in artifact) | Likely placeholder | ⚠️ AUDIT |
| **Radar page body** | Full Radar UI (exists in artifact) | Likely placeholder | ⚠️ AUDIT |
| **Patrimonio page body** | Full Patrimonio UI (exists in artifact) | Likely placeholder | ⚠️ AUDIT |
| **Flujo-detalle page** | Full transaction flow UI (exists in artifact) | Likely placeholder | ⚠️ AUDIT |
| **CashTodayCard component** | Rendered in Overview with mock values | Should exist but needs live-data binding | ⚠️ EXTEND |
| **Service worker** | Versioned (`CACHE_VERSION` in `sw.js`) | Exists, may need version bump | ✓ TOUCH |
| **API client** | Implicit in injected script | `lib/api-client.ts` has `fetchFinancials()` | ✓ GOOD |
| **Logout label** | "Cerrar Sesión" (UTF-8 verified in artifact HTML) | Must verify in source | ⚠️ CHECK |

### Next Step (Task 1.3)

Verify `contexia-app/` source is complete (no `.gitignore` trap). If any top-level components are missing (layout, TopBar, page structures), source them from the `app/` export or git history.

---

## Task 1.3: Confirm `contexia-app/` source completeness

**Status:** Pending

To be done:
- [ ] `git status` in `contexia-app/` (check for missing files due to `.gitignore`)
- [ ] Verify key files exist: `components/layout/TopBar.tsx`, `components/layout/BottomNav.tsx`, all 5 page files
- [ ] If files are missing, restore from `app/` export or git history (never fabricate stubs per CLAUDE.md §9)
