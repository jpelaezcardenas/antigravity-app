import type { LiquidityBridge } from "@/lib/types/contexia";
import { formatCop } from "@/lib/format";

export function MonthlyLiquidityBridgeCard({
  bridge,
}: {
  bridge: LiquidityBridge;
}) {
  return (
    <section className="bg-surface-elevated border border-white/5 rounded-xl p-6 flex flex-col gap-4">
      <h3 className="font-label-caps text-label-caps text-primary-container uppercase tracking-wider mb-2">
        Puente de Liquidez (Mensual)
      </h3>
      <div className="flex flex-col gap-3 font-data-mono text-data-mono">
        <div className="flex justify-between items-center py-2 border-b border-surface-variant">
          <span className="text-on-surface-variant font-body-md text-body-md">
            Saldo Inicial
          </span>
          <span className="text-on-surface">
            {formatCop(bridge.initialBalance)}
          </span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-surface-variant">
          <span className="text-on-surface-variant font-body-md text-body-md">
            Ingresos
          </span>
          <span className="text-status-success">
            + {formatCop(bridge.inflows)}
          </span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-surface-variant">
          <span className="text-on-surface-variant font-body-md text-body-md">
            Egresos
          </span>
          <span className="text-status-critical">
            {formatCop(bridge.outflows)}
          </span>
        </div>
        <div className="flex justify-between items-center pt-2 mt-1">
          <span className="text-on-surface font-title-md text-title-md">
            Saldo Final
          </span>
          <span className="text-primary font-title-md text-title-md">
            {formatCop(bridge.finalBalance)}
          </span>
        </div>
      </div>
    </section>
  );
}
