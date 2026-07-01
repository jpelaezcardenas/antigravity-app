## ADDED Requirements

### Requirement: PWA rebuildable from source with full client UI

The end-user PWA SHALL be fully reproducible from the `contexia-app/` source: running `npm run build` and syncing `contexia-app/out/` → `app/` MUST yield the exact production UI currently served at `contexia.online/app/overview`, with no hand-edits to `app/`.

#### Scenario: Rebuild reproduces the full top navigation
- **WHEN** `contexia-app` is built and the output is served
- **THEN** the header renders the Contexia logo and the nav items Pulso, Fiscal, Radar and Patrimonio, the "AUDITORÍA SOMBRA (SIMULACIÓN CON LA DIAN)" CTA, the "Tu Amiga Contadora / Taty" card, and a "Cerrar Sesión" action

#### Scenario: Logout label is correct UTF-8
- **WHEN** the rebuilt overview page renders the logout control
- **THEN** its label is exactly "Cerrar Sesión" (valid UTF-8, no `U+FFFD` replacement character)

#### Scenario: No hand-edited artifact remains
- **WHEN** the reconciled source is built and synced to `app/`
- **THEN** `app/overview.html` contains no hand-injected `<script>` for data wiring, and a `git diff` between the synced output and the committed `app/` shows only build-generated content

### Requirement: Caja Real renders live data as a first-class component

The Pulso/Overview screen SHALL fetch `GET /api/v1/financials` from a data-bound component (not an injected script) and display `caja_real`, `dinero_disponible`, `ventas_ayer` and `gastos_ayer`, converting minor units (cents) to COP by dividing by 100.

#### Scenario: Live values shown when backend responds
- **WHEN** `GET /api/v1/financials` returns `{caja_real: 352000000, dinero_disponible: 352000000, ventas_ayer: 0, gastos_ayer: 0, status: "healthy"}`
- **THEN** the screen shows "Caja Real de Hoy: $3.520.000", "Dinero tuyo de verdad: $3.520.000", "Ventas de ayer: $0" and "Salidas de plata: $0"

#### Scenario: Daily granularity preserved
- **WHEN** the component maps the response
- **THEN** `ventas_ayer` / `gastos_ayer` are rendered as the prior-day figures only (not a monthly aggregate), matching the backend contract

### Requirement: Live fetch degrades gracefully, never to an error banner

The Caja Real component SHALL expose explicit loading, ready, empty and error states, and MUST NOT display the "No pudimos cargar tu caja real" failure state to the end user when the fetch fails; it falls back to a neutral placeholder.

#### Scenario: Backend unreachable
- **WHEN** the `GET /api/v1/financials` request fails (network error, CORS, timeout, or non-2xx)
- **THEN** the screen shows a neutral non-error state (skeleton or last-known/placeholder value) and no red error message is shown to the client

#### Scenario: Empty tenant data
- **WHEN** the backend responds with `status: "empty"` or zeroed figures
- **THEN** the screen renders a defined empty state rather than crashing or showing an error

### Requirement: Service worker versioned per deploy

The PWA service worker SHALL bump `CACHE_VERSION` on any deploy that changes cached assets and MUST use network-first for navigation/HTML.

#### Scenario: New deploy invalidates stale cache
- **WHEN** a build changes the HTML shell or `/_next/static/` assets and is deployed
- **THEN** `CACHE_VERSION` differs from the previous deploy, the activate handler purges old caches, and returning clients receive the new HTML via network-first
