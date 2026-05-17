import type { FinancialHealthMetric } from "@/lib/types/contexia";
import {
  STATUS_HEALTH_BADGE,
  STATUS_BADGE_LABEL,
  FLOW_COLOR_CONFIG,
} from "@/lib/styles/statusStyles";

export function FinancialHealthStatusGrid({
  metrics,
}: {
  metrics: FinancialHealthMetric[];
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {metrics.map((metric) => {
        const badgeConfig = STATUS_HEALTH_BADGE[metric.status];
        const colorConfig = FLOW_COLOR_CONFIG[metric.color];

        return (
          <div
            key={metric.id}
            className="bg-surface-elevated border border-white/5 rounded-xl p-5 flex flex-col gap-3"
          >
            <div className="flex justify-between items-start">
              <h4 className="font-title-md text-title-md text-primary-container">
                {metric.label}
              </h4>
              <span
                className={`px-2 py-1 rounded-md ${badgeConfig.bg} ${badgeConfig.text} border font-label-caps text-label-caps`}
              >
                {STATUS_BADGE_LABEL[metric.status]}
              </span>
            </div>
            <p className="font-body-md text-[14px] leading-tight text-on-surface-variant">
              {metric.description}
            </p>
            <div className="mt-2 h-1.5 w-full bg-surface-variant rounded-full overflow-hidden">
              <div
                className={`h-full ${colorConfig.bg} rounded-full ${colorConfig.shadow}`}
                style={{ width: `${metric.percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
