import { flujoDetalleMock } from "@/lib/mock/flujoDetalle";
import { StructuralInsightCard } from "@/components/flujo-detalle/StructuralInsightCard";
import { FlowCompositionCard } from "@/components/flujo-detalle/FlowCompositionCard";
import { MonthlyLiquidityBridgeCard } from "@/components/flujo-detalle/MonthlyLiquidityBridgeCard";
import { FinancialHealthStatusGrid } from "@/components/flujo-detalle/FinancialHealthStatusGrid";
import { TatyActionBar } from "@/components/flujo-detalle/TatyActionBar";

export default function FlujoDetallePage() {
  const data = flujoDetalleMock;

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-3xl mx-auto flex flex-col gap-6 w-full pb-32">
      {/* Header Context */}
      <div className="flex flex-col gap-2 mt-6">
        <h2 className="font-title-md text-title-md text-primary-container">
          {data.header.title}
        </h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          {data.header.subtitle}
        </p>
      </div>

      {/* AI Insight Narrative */}
      <StructuralInsightCard insight={data.insight} />

      {/* Structural Flow Breakdown */}
      <FlowCompositionCard items={data.flowComposition} />

      {/* Cash Flow Waterfall / Bridge */}
      <MonthlyLiquidityBridgeCard bridge={data.liquidityBridge} />

      {/* Health Quadrant Details */}
      <FinancialHealthStatusGrid metrics={data.healthMetrics} />

      {/* Sticky CTA + Drawer */}
      <TatyActionBar />
    </div>
  );
}
