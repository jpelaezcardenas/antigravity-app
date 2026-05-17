import type { FlowCompositionItem } from "@/lib/types/contexia";
import { FLOW_COLOR_CONFIG } from "@/lib/styles/statusStyles";

export function FlowCompositionCard({
  items,
}: {
  items: FlowCompositionItem[];
}) {
  return (
    <section className="bg-surface-elevated border border-white/5 rounded-xl p-6 flex flex-col gap-6 shadow-lg">
      <h3 className="font-label-caps text-label-caps text-primary-container uppercase tracking-wider">
        Composición del Flujo
      </h3>
      <div className="flex flex-col gap-5">
        {items.map((item) => {
          const config = FLOW_COLOR_CONFIG[item.color];
          const absPercentage = Math.abs(item.percentage);

          return (
            <div key={item.id} className="flex flex-col gap-2">
              <div className="flex justify-between items-end">
                <span className="font-body-md text-body-md text-on-surface flex items-center gap-2">
                  <span
                    className={`w-3 h-3 rounded-full ${config.bg} ${config.dot}`}
                  />
                  {item.label}
                </span>
                <span className={`font-data-mono text-data-mono ${item.color}`}>
                  {item.percentage > 0 ? "+" : ""}
                  {item.percentage}%
                </span>
              </div>
              <div className="h-2 w-full bg-surface-variant rounded-full overflow-hidden">
                <div
                  className={`h-full ${config.bg} rounded-full ${config.shadow}`}
                  style={{ width: `${absPercentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
