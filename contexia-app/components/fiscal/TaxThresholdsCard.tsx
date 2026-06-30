import type { UvtThreshold } from "@/lib/types/contexia";
import { ProgressBar, variantFromUsage } from "@/components/ui/ProgressBar";

function getTextColor(percent: number): string {
  if (percent >= 85) return "text-status-critical";
  if (percent >= 70) return "text-status-warning";
  return "text-primary-container";
}

function formatUvt(value: number): string {
  // Formato 1.400 (separador de miles con punto, estilo es-CO)
  return value.toLocaleString("es-CO");
}

export function TaxThresholdsCard({
  thresholds,
}: {
  thresholds: UvtThreshold[];
}) {
  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <span className="material-symbols-outlined text-primary-container">
          data_usage
        </span>
        <h3 className="font-title-md text-title-md text-primary-container">
          Límites Tributarios (UVT)
        </h3>
      </div>

      <div className="flex flex-col gap-5">
        {thresholds.map((threshold) => {
          const percent = (threshold.current / threshold.max) * 100;
          const variant = variantFromUsage(percent);
          const textColor = getTextColor(percent);
          return (
            <div key={threshold.id} className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <span className="font-label-caps text-label-caps text-on-surface-variant">
                  {threshold.label}
                </span>
                <span
                  className={`font-data-mono text-data-mono ${textColor}`}
                >
                  {formatUvt(threshold.current)} / {formatUvt(threshold.max)}{" "}
                  {threshold.unit}
                </span>
              </div>
              <ProgressBar percent={percent} variant={variant} />
            </div>
          );
        })}
      </div>
    </section>
  );
}
