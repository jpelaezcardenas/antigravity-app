import { patrimonio } from "@/lib/mock/patrimonio";
import { StrategicPatrimonyInsightCard } from "@/components/patrimonio/StrategicPatrimonyInsightCard";
import { WithdrawalSimulatorCard } from "@/components/patrimonio/WithdrawalSimulatorCard";
import { EquityMovementHistoryCard } from "@/components/patrimonio/EquityMovementHistoryCard";
import { UpgradePlanBannerV2 } from "@/components/shared/v2/UpgradePlanBannerV2";
import { V2ConfigGearHeader } from "@/components/shared/v2/V2ConfigGearHeader";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";
import { MetricTileGrid, type MetricTile } from "@/components/shared/v2/MetricTileGrid";
import { formatCop } from "@/lib/format";

/**
 * PWA V2 visual pilot (Fase 3, reconstructed 2026-09-17) — the first cut of
 * this page reused old V1 card components (TotalEquityCard, DividendShieldCard)
 * verbatim with just a new hero on top, which is NOT what was approved in
 * Stitch: a compact 2-column metric-tile grid (Weather UV/Humidity/Real Feel
 * pattern). This version replaces those two cards with a real tile grid —
 * every value still comes straight from the same `patrimonio` mock, nothing
 * invented. StrategicPatrimonyInsightCard, WithdrawalSimulatorCard (real
 * slider logic) and EquityMovementHistoryCard stay below the grid as depth
 * beyond the single Stitch screenshot, not V1 leftovers.
 */
export default function PatrimonioV2Page() {
  const data = patrimonio;

  const tiles: MetricTile[] = [
    {
      id: "retained-earnings",
      icon: "savings",
      label: "Utilidades retenidas",
      value: formatCop(data.patrimonio.retainedEarnings),
    },
    {
      id: "current-year-earnings",
      icon: "trending_up",
      label: "Utilidad del ejercicio",
      value: formatCop(data.patrimonio.currentYearEarnings),
      accent: "success",
    },
    {
      id: "safe-withdrawal",
      icon: "shield",
      label: "Retiro seguro máximo",
      value: formatCop(data.dividendShield.safeAmount),
    },
    {
      id: "cash-with-withdrawal",
      icon: "account_balance_wallet",
      label: "Caja con retiro",
      value: formatCop(data.withdrawalSimulator.cashWithoutWithdrawal),
    },
  ];

  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2 pb-16"
    >
      <V2ConfigGearHeader />

      <UpgradePlanBannerV2 />

      <section className="flex flex-col gap-1.5">
        <p className="text-xs font-medium tracking-widest uppercase text-on-surface-variant/90">
          Patrimonio total
        </p>
        <h1 className="font-extralight tracking-tight text-white text-[40px] sm:text-[48px] leading-tight">
          {formatCop(data.patrimonio.total)}
        </h1>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container/60 border border-outline-variant/40 backdrop-blur-md w-fit">
          <span className="material-symbols-outlined text-primary text-[14px]">
            pie_chart
          </span>
          <span className="text-xs font-normal text-on-surface-variant tracking-wide">
            Composición del capital
          </span>
        </div>
      </section>

      <JarvisFloatingBadgeV2 />

      <MetricTileGrid tiles={tiles} />

      <StrategicPatrimonyInsightCard insight={data.insight} />
      <WithdrawalSimulatorCard
        initialWithdrawal={data.withdrawalSimulator}
        cashWithoutWithdrawal={data.withdrawalSimulator.cashWithoutWithdrawal}
      />
      <EquityMovementHistoryCard movements={data.movements} />
    </div>
  );
}
