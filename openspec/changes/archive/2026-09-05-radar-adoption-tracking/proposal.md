## Why

`radar-cash-projection-13w` shipped the Radar de Caja but descoped its last acceptance
criterion: *"Se agrega un evento de analítica/tracking simple para medir adopción (apertura
del módulo por tenant/semana) — esto alimenta el KPI de ≥40% de usuarios activos abren
Radar de Caja al menos 1x/semana"*. It was descoped because `contexia-app` has no analytics
pattern to reuse and inventing one mid-change would have been unauthorized scope. That
change is now archived, so this closes the gap as its own delta.

Without it there is no way to answer "is anyone using this?" — the module's whole validation
KPI is unmeasurable.

## What Changes

- New table `radar_module_opens` (migration `0047`): one row per tenant + user + day, with
  **real tenant-scoped RLS** following migration `0045`'s policy pattern — deliberately not
  the permissive `USING (true)` shape the Shadow GL tables carry (see the masterprompt audit).
- `GET /api/v1/radar/proyeccion-caja` records an open for the resolved tenant as a side
  effect. Deduplicated per tenant+user+day by a unique constraint, so repeated loads and
  refetches on the same day are one row, and the table cannot grow per-render.
- The recording is **fail-soft**: any error writing the event is logged and swallowed. A
  telemetry failure must never break a client's cash projection.
- No frontend change. Recording server-side means zero new client round-trip, nothing for a
  future screen to forget to call, and no new dependency in `contexia-app` — which its own
  hard rules forbid without strong reason.

## Non-Goals

- No admin dashboard or chart for adoption. The KPI query is documented in `design.md`;
  surfacing it in the Búnker is a separate decision.
- No general-purpose analytics pipeline, event bus, or third-party tracker. This is one
  table for one KPI.
- No PII beyond the `auth.uid()` already present throughout the system.
- Does not change the projection's behaviour, response shape, or the archived spec.

## Capabilities

### New Capabilities
- `radar-adoption-tracking`: per-tenant/per-user/per-day recording of Radar de Caja opens,
  written as a fail-soft side effect of the projection endpoint, with tenant-scoped RLS.

### Modified Capabilities
(none — `radar-cash-projection`'s requirements are unchanged; this adds a side effect that
its spec neither requires nor forbids)

## Impact

- DB: new table `radar_module_opens` + migration `0047_radar_module_opens.sql`. Additive;
  no existing table or row is touched.
- Backend: `services/radar_service.py` (new `record_module_open`),
  `presentation/radar_endpoints.py` (call it), new tests.
- Frontend: none.
- Deploy: Railway only. Stage 11 applies; the migration needs explicit founder approval
  before being applied to production, per this repo's practice for schema changes.
