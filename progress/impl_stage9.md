# Stage 9 implementation report — MonthlyLiquidityBridgeCard becomes data-bound

## Task
`openspec/changes/pwa-tenant-aware-screens/tasks.md` Stage 9 (9.1–9.3).

## Files touched

- `contexia-app/components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx`
- `contexia-app/app/flujo-detalle/page.tsx`

## What changed

### `MonthlyLiquidityBridgeCard.tsx`
- Converted to `"use client"`, self-feeding component (dropped the `bridge: LiquidityBridge`
  prop entirely).
- `useEffect` on mount calls `fetchLiquidityBridge()` (`lib/api-client.ts`, added in Stage 7),
  with a `cancelled` guard identical to `CashTodayCard`'s pattern.
- Three explicit states via a `status: "loading" | "ready" | "unavailable"` state variable:
  - **loading**: skeleton with 4 pulsing bars (one per row: Saldo Inicial / Ingresos / Egresos /
    Saldo Final), `animate-pulse` + `bg-white/10` bars, same visual language as
    `CashTodayCard`'s skeleton.
  - **ready**: same 4-row layout the card already had, now sourced from
    `LiquidityBridgeSnapshot` (`initial_balance`, `inflows`, `outflows`, `final_balance`, all
    COP minor units), each divided by 100 before `formatCop`.
  - **unavailable** (fetch throws, i.e. `.catch`, OR `snapshot.status === "empty"`): renders
    "Datos no disponibles por el momento." inside the card's existing header/border chrome — does
    **not** render `flujoDetalleMock.liquidityBridge` or any other figure. Unlike
    `CashTodayCard`'s pre-Stage-10 behavior, this card never falls back to mock data on error,
    per spec `client-pwa-live-data` scenario "Unavailable state renders honestly, never a mock
    value" (design.md D5 precedent).

### Sign/formatting convention for outflows
The old mock stored `outflows: -112300` (already negative) and rendered it via
`formatCop(bridge.outflows)` — i.e. `formatCop` was fed a negative number directly, producing a
signed output styled red (`text-status-critical`), with no `+`/`-` literal prefix (unlike
Ingresos, which prepends a literal `+ `).

The new `LiquidityBridgeSnapshot.outflows` field is a **positive** sum of credits per the
backend's `compute_liquidity_bridge` (Stage 3). To preserve the exact prior visual convention
(a negative-signed figure via `formatCop`, no manual `+`/`-` string prefix), I negate before
formatting: `formatCop(-(bridge.outflows / 100))`. Ingresos keeps the literal `+ ` prefix
unchanged, matching the pre-existing pattern.

### `app/flujo-detalle/page.tsx`
- `<MonthlyLiquidityBridgeCard bridge={data.liquidityBridge} />` → `<MonthlyLiquidityBridgeCard />`.
- Page remains a Server Component; `flujoDetalleMock` import kept as-is (still used by
  `StructuralInsightCard`, `FlowCompositionCard`, `FinancialHealthStatusGrid` on the same page —
  untouched). `data.liquidityBridge` is now simply unused by this page, which is expected and
  fine (mock data itself untouched, still used by any consumers of `lib/mock/flujoDetalle.ts`
  elsewhere if any).

## Verification

```
$ cd contexia-app && npx tsc --noEmit
(no output — clean)
```

`node_modules` already present in the worktree (Stage 7 install), no new dependency added.

## Scope discipline
Only the 2 files above were staged/committed. `git status` before staging showed
`contexia-app/components/pulso/CashTodayCard.tsx` as modified in the working tree (concurrent
Stage 10 agent's WIP) and untracked `progress/impl_stage7.md`, `progress/review_stage7.md`,
`progress/impl_stage8.md` (concurrent agents' output) — none of these were touched, staged, or
committed by this task. `git diff` on `CashTodayCard.tsx` showed no actual content difference
(line-ending flag only) at the time of my check.

## Commit
`095a771` — "feat(pwa-tenant-aware-screens): MonthlyLiquidityBridgeCard becomes data-bound"

## Not done (out of scope for this task)
- Task 9.3 formally requires `npx tsc --noEmit` clean only — confirmed above. Did not run
  `npm run build` (that's Stage 10.2's full-build gate, owned by the concurrent CashTodayCard
  task).
- tasks.md checkboxes were **not** checked off — per instructions, leader/reviewer does that.
