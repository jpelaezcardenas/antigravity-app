# Review — Stage 8: ActiveAlerts becomes data-bound

**Verdict:** APPROVED

## Scope

Commit `d8d6747` — `feat(pwa-tenant-aware-screens): ActiveAlerts becomes data-bound`.
`git show --stat d8d6747` confirms exactly 2 files touched:
- `contexia-app/components/pulso/ActiveAlerts.tsx`
- `contexia-app/app/app/(shell)/overview/page.tsx`

No encroachment on `CashTodayCard.tsx`, `MonthlyLiquidityBridgeCard.tsx`, or
`flujo-detalle/page.tsx` (Stages 9/10 concurrent work). `git status --porcelain`
on the current worktree HEAD is clean.

## Checkpoints

- C1 (spec: "Live alerts replace the mock"): [x] — `ActiveAlerts.tsx:37-62` is
  `"use client"`, self-feeding via `fetchCentinelaAlerts()`
  (`contexia-app/lib/api-client.ts:70-84`) in a `useEffect` with a `cancelled`
  guard, mirroring `CashTodayCard.tsx:27-52`. The `alerts` prop is fully
  removed (`overview/page.tsx:16` now renders `<ActiveAlerts />` with no
  props); the component signature is `export function ActiveAlerts()`
  (`ActiveAlerts.tsx:37`).
- C2 (spec: "No alerts or a fetch error renders nothing... SHALL NOT fall back
  to `pulsoMock.alerts`"): [x] — grepped `ActiveAlerts.tsx` independently for
  `pulsoMock`: zero matches (the only occurrences of the string "pulsoMock"
  are inside a code comment describing the spec requirement, not a live
  reference/import). On fetch failure (`ActiveAlerts.tsx:50-57`), `alerts` is
  set to `[]` and status becomes `"ready"`, which falls through to
  `alerts.length === 0 → return null` at line 68. Zero alerts from a
  successful-but-empty response takes the same path. Matches both spec
  scenarios verbatim (no crash, no mock, renders nothing).
- C3 (severity mapping / message composition): [x] — `toSeverity` maps
  `"critical"` → `"critical"`, everything else (including backend `"info"`)
  → `"warning"` (`ActiveAlerts.tsx:13-15`), matching the local 2-value
  `AlertSeverity` union (`lib/types/contexia.ts:8`) and
  `SEVERITY_ICON_STYLES` (`statusStyles.ts:59-70`), which has no `"info"`
  entry — widening the union was correctly identified as out of scope.
  `message` composes `${title} — ${description}` when `description` is
  present, else just `title` (`ActiveAlerts.tsx:23`) — no information the
  card UI can display is silently dropped. `recommendation`/`evidence` are
  intentionally unsurfaced since the existing card has no expand affordance
  wired up; reasonable and documented.
- C4 (overview page wiring): [x] — `<ActiveAlerts />` with no props
  (`overview/page.tsx:16`); `pulsoMock` import retained and still used by
  `pulsoMock.note` (line 12) and `pulsoMock.health` (line 14) on the same
  page — correctly not orphaned, correctly not over-removed.
- C5 (typecheck): [x] — ran `cd contexia-app && npx tsc --noEmit` myself:
  clean, exit code 0.
- C6 (no scope creep): [x] — confirmed via `git show --stat d8d6747`, exactly
  the 2 expected files; no diff on `CashTodayCard.tsx`,
  `MonthlyLiquidityBridgeCard.tsx`, or `flujo-detalle/page.tsx`.
- C7 (English-only, fully typed, `@theme` tokens): [x] — all identifiers,
  comments, and strings in the diff are English (UI copy in Spanish is the
  established founder-facing product convention already used throughout
  `contexia-app`, not new here). No ad-hoc hex/rgb colors introduced — every
  class is an existing token utility (`bg-surface-elevated`,
  `text-on-surface`, `border-white/10`, `font-body-md`, etc.), consistent
  with `CashTodayCard`'s pattern. `CentinelaAlert`, `toActiveAlert`,
  `toSeverity` are fully typed with no `any`.
- Docs-sync: [x] — no container/dependency change; `ARCHITECTURE.md` does not
  need updating for this stage (already covers the `/api/v1/*` financials
  flow; alerts endpoint is an existing backend route, not a new dependency).

## Notes (non-blocking)

- `id: alert.rule_id || `alert-${index}`` uses `||`, not `??` — if a future
  backend ever returns `rule_id: ""` this still falls back to the index key,
  which is actually the desired behavior here (empty string is as unusable as
  null/undefined for a React key), so this is fine as written, not a defect.
- The icon-by-severity approximation (losing per-rule icon specificity) is a
  reasonable, explicitly documented tradeoff given the backend has no icon
  field — does not violate the spec, which only requires "mapped to the
  existing card UI."

No required changes.
