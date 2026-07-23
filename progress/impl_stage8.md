# Stage 8 — ActiveAlerts becomes data-bound

## Files touched
- `contexia-app/components/pulso/ActiveAlerts.tsx` — rewritten as a self-feeding `"use client"`
  component following the `CashTodayCard` pattern exactly.
- `contexia-app/app/app/(shell)/overview/page.tsx` — `<ActiveAlerts alerts={pulsoMock.alerts} />`
  → `<ActiveAlerts />`. `pulsoMock` import kept (still used by `pulsoMock.note` and
  `pulsoMock.health` on this page — out of scope, untouched).

## What changed
- Dropped the `alerts` prop; component now calls `fetchCentinelaAlerts()` (`lib/api-client.ts`,
  Stage 7) in a `useEffect` on mount, with a `cancelled` guard matching `CashTodayCard`.
- Added a `"loading" | "ready"` status state (no separate "empty"/"error" state needed — both
  collapse to `alerts.length === 0 → return null`, per the spec's "renders nothing" scenario and
  the existing pre-Stage-8 `if (alerts.length === 0) return null` behavior).
- On fetch failure: `console.warn` + set `alerts` to `[]` (never falls back to `pulsoMock.alerts`
  — matches the honesty rule Stage 10 is separately restoring for `CashTodayCard`, so no
  regression is reintroduced here).
- Added `AlertsSkeleton` (pulsing header bar + two pulsing 16px-tall bars) for the loading state,
  visually consistent with `CashTodayCard`'s `animate-pulse` skeleton pattern but sized for this
  section's row-list shape rather than a single stat block.

## Field-mapping decisions
- **`id`**: backend `CentinelaAlert` has no `id`. Used `rule_id` (documented as "unique per alert
  rule row" in Stage 2/6's backend work) with an index-based fallback (`alert-${index}`) only if
  `rule_id` is falsy — avoids duplicate React keys without assuming uniqueness that isn't
  guaranteed by the type.
- **`severity`**: local `AlertSeverity` type is `"warning" | "critical"` only (2 values); backend
  sends a free string (`"info" | "warning" | "critical"`). Mapped `"critical"` → `"critical"`,
  everything else (including `"info"` and any unexpected value) → `"warning"`, per the task's
  explicit instruction — no `SEVERITY_ICON_STYLES` entry exists for `"info"`, so widening the
  local union wasn't an option without touching shared style files (out of scope).
- **`icon`**: `SEVERITY_ICON_STYLES` (`lib/styles/statusStyles.ts`) only supplies border/bg/text
  color classes, not the Material Symbols glyph name — the glyph itself was always a per-alert
  choice in the mock (`schedule` for the IVA-deadline warning, `rule_folder` for the
  unclassified-transactions critical alert). Since the backend gives no icon field, mapped by
  *severity* to one representative glyph per bucket: `warning → schedule` (matches the mock's
  existing warning-severity icon, reads as "time-sensitive"), `critical → rule_folder` (matches
  the mock's existing critical-severity icon, reads as "needs review/organizing"). This loses
  per-rule icon specificity but is consistent, typed, and doesn't invent unreviewed status-icon
  mappings.
- **`message`**: backend has separate `title` + `description` (+ optional `recommendation`,
  unused here). Used `` `${title} — ${description}` `` when `description` is present, else just
  `title`, so no information is silently dropped versus the single-line mock message the card UI
  was built to display. `recommendation` and `evidence` are intentionally not surfaced — the
  existing card UI has one text line + a "ver detalle" chevron with no expand/drawer wired up
  (out of scope for this task; the chevron button remains inert, same as before Stage 8).

## Verification
```
$ cd contexia-app && npx tsc --noEmit
(clean — no output, exit 0)
```

`node_modules` already present in this worktree (from Stage 7); no `npm install` needed, no new
dependencies added.

## Scope check
- Only `contexia-app/components/pulso/ActiveAlerts.tsx` and
  `contexia-app/app/app/(shell)/overview/page.tsx` staged and committed.
- `contexia-app/components/pulso/CashTodayCard.tsx` is modified in the working tree by a
  concurrent Stage 10 agent — left untouched and unstaged, confirmed via `git status --porcelain`
  before `git add`.
- Did not touch `MonthlyLiquidityBridgeCard.tsx`, `flujo-detalle/page.tsx`, or any backend/lib
  file (only read `lib/api-client.ts` and `lib/styles/statusStyles.ts`, per instructions).
- `tasks.md` left unchecked (8.1/8.2/8.3), per instructions — not marking done myself.

## Commit
`d8d6747` — `feat(pwa-tenant-aware-screens): ActiveAlerts becomes data-bound`
(branch `feature/pwa-tenant-aware-screens`, worktree
`antigravity-app-pwa-tenant-aware-screens`)
