# Review — Stage 9 (MonthlyLiquidityBridgeCard becomes data-bound)

**Verdict:** APPROVED

## Scope verified
- `git show --stat 095a771` — exactly 2 files touched: `contexia-app/components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx` and `contexia-app/app/flujo-detalle/page.tsx`. `git log -1 -- CashTodayCard.tsx ActiveAlerts.tsx overview/page.tsx` shows their last touch was `014b740`/`d8d6747` — Stage 9 did not touch Stage 8/10 files. `git status` on the worktree is clean.

## Checkpoint-by-checkpoint

1. **Client-side, self-feeding, prop removed** — Confirmed. `MonthlyLiquidityBridgeCard.tsx:1` is `"use client"`; `useEffect` (lines 16-41) calls `fetchLiquidityBridge()` from `lib/api-client.ts` with a `cancelled` guard identical in shape to `CashTodayCard`. The component signature is `MonthlyLiquidityBridgeCard()` — zero props, `bridge` prop fully removed (confirmed by diff and by `page.tsx:29` calling it with no props).

2. **Sign convention — verified both halves independently, claim is correct:**
   - **Old mock**: `git show 095a771~1:contexia-app/lib/mock/flujoDetalle.ts` → `outflows: -112300` (negative), confirming the pre-change value was signed negative and fed straight into `formatCop(bridge.outflows)` for red-styled signed output with no literal `-` prefix.
   - **Backend**: `apps/backend/services/financials_service.py:179-181` — `inflows = sum(debit_minor...)`, `outflows = sum(credit_minor...)`, `final_balance = initial_balance + inflows - outflows`. The arithmetic (`+inflows -outflows`) only holds if `outflows` is a positive magnitude, and `debit_minor`/`credit_minor` are used elsewhere in the same file (lines 45, 56-62) as non-negative ledger amounts summed directly (`ventas += credit_minor`, `salidas += debit_minor`) — standard double-entry convention, never negative.
   - **New code**: `formatCop(-(bridge.outflows / 100))` at line 99 negates the positive backend value before formatting, exactly reproducing the old mock's negative-signed red output. This is correct — not backwards. Ingresos keeps its literal `+ ` prefix on a positive value (line 91), unchanged from before.
   - No double-negation, no off-by-sign risk found.

3. **Unavailable state, no mock fallback** — Grepped the file directly (`grep -n flujoDetalleMock MonthlyLiquidityBridgeCard.tsx`): only one hit, and it's inside a comment (line 31), not an import or reference. `.catch` (line 29-36) and `snapshot.status === "empty"` (line 22-25) both route to `status: "unavailable"`, which renders "Datos no disponibles por el momento." (line 66) with no numeric fallback. Matches spec scenario "Unavailable state renders honestly, never a mock value" (`specs/client-pwa-live-data/spec.md:23-26`).

4. **`page.tsx` stays a Server Component** — Read in full: no `"use client"` directive, `data = flujoDetalleMock` still drives `StructuralInsightCard`, `FlowCompositionCard`, `FinancialHealthStatusGrid` unchanged (lines 23, 26, 32), and `<MonthlyLiquidityBridgeCard />` (line 29) is now prop-less. Matches spec: "other cards... MAY continue to use mocks in this slice."

5. **`npx tsc --noEmit`** — ran independently from `contexia-app/`: clean, no output.

6. **Scope isolation** — Confirmed via `git show --stat` and `git log -1` on the three sibling files above; no encroachment.

7. **English-only / fully typed / tokens** — All identifiers, comments, and types are English (`CardStatus`, `LiquidityBridgeSnapshot`, etc.); only end-user-facing UI copy ("Puente de Liquidez (Mensual)", "Datos no disponibles por el momento.") is Spanish, consistent with the existing `CashTodayCard` pattern and the rest of the client PWA. All classNames use the same `@theme` token classes already in use pre-change (`bg-surface-elevated`, `text-status-critical`, `text-status-success`, `font-title-md`, etc.) plus a plain `animate-pulse`/`bg-white/10` skeleton matching `CashTodayCard`'s established skeleton idiom. Fully typed: `LiquidityBridgeSnapshot | null` state, `CardStatus` union, no `any`.

## Spec scenario coverage
- "Live bridge replaces the mock" — satisfied (ready branch renders `bridge.*` fields, never `flujoDetalleMock.liquidityBridge`).
- "Loading state" — satisfied (skeleton branch, no stale/mock figures).
- "Unavailable state renders honestly, never a mock value" — satisfied, see #3 above.

## Required changes
None.
