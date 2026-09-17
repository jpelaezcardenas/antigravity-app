import { flujoDetalleMock } from "@/lib/mock/flujoDetalle";
import { StructuralInsightCard } from "@/components/flujo-detalle/StructuralInsightCard";
import { FlowCompositionCard } from "@/components/flujo-detalle/FlowCompositionCard";
import { MonthlyLiquidityBridgeCard } from "@/components/flujo-detalle/MonthlyLiquidityBridgeCard";
import { FinancialHealthStatusGrid } from "@/components/flujo-detalle/FinancialHealthStatusGrid";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";

/**
 * PWA V2 pilot (Fase 4) — reuses flujoDetalleMock and every existing
 * component verbatim, including the real MonthlyLiquidityBridgeCard.
 * Same hero framing pattern as the other -v2 routes, applied directly in
 * code (no separate Stitch round for this secondary/detail screen).
 */
export default function FlujoDetalleV2Page() {
  const data = flujoDetalleMock;

  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop max-w-3xl mx-auto flex flex-col gap-6 w-full pb-12"
    >
      <div className="flex flex-col gap-1.5 mt-6">
        <p className="text-xs font-medium tracking-widest uppercase text-on-surface-variant/90">
          {data.header.title}
        </p>
        <p className="text-on-surface-variant text-sm font-normal">{data.header.subtitle}</p>
      </div>

      <JarvisFloatingBadgeV2 />

      <StructuralInsightCard insight={data.insight} />
      <FlowCompositionCard items={data.flowComposition} />
      <MonthlyLiquidityBridgeCard />
      <FinancialHealthStatusGrid metrics={data.healthMetrics} />
    </div>
  );
}
