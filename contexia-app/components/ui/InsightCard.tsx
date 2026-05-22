import type { Insight } from "@/lib/types/contexia";
import { CARD_SHADOW } from "@/lib/styles/cardStyles";

type InsightVariant = "elevated" | "accent" | "gradient";

/**
 * Tarjeta de insight genérica para Radar, Patrimonio y FlujoDetalle
 * Reemplaza: StrategicInsightCard, StrategicPatrimonyInsightCard, StructuralFlowInsightCard
 *
 * Variants:
 * - "elevated": Simple elevated surface (default, FlujoDetalle style)
 * - "accent": Left border accent with glass effect (structural/flow insights)
 * - "gradient": Gradient border with label header (strategic/radar insights)
 */
export function InsightCard({
  insight,
  variant = "elevated",
  showLabel = false,
  label = "Insight Estratégico",
}: {
  insight: Insight;
  variant?: InsightVariant;
  showLabel?: boolean;
  label?: string;
}) {
  // Elevated variant: simple, clean surface
  if (variant === "elevated") {
    return (
      <div className={`bg-surface-elevated rounded-xl border border-white/10 p-5 flex flex-col gap-3 ${CARD_SHADOW.base}`}>
        <div className="flex items-start gap-3">
          <span
            className="material-symbols-outlined text-primary animate-pulse flex-shrink-0"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            auto_awesome
          </span>
          <div className="flex flex-col gap-2 flex-1 min-w-0">
            {insight.body.map((segment, idx) => (
              <p
                key={idx}
                className={`font-body-md text-body-md ${
                  segment.highlight ? "text-primary font-semibold" : "text-on-surface"
                }`}
              >
                {segment.text}
              </p>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Accent variant: left border with glass effect
  if (variant === "accent") {
    return (
      <div className="glass-panel rounded-xl p-6 relative overflow-hidden ai-glow border-ai-narrative-tint/20">
        <div className="absolute top-0 left-0 w-1 h-full bg-ai-narrative-tint"></div>
        <div className="flex gap-4 items-start">
          <div className="mt-1 flex-shrink-0">
            <span
              className="material-symbols-outlined text-ai-narrative-tint"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              auto_awesome
            </span>
          </div>
          <div className="flex flex-col gap-2">
            <p className="font-body-md text-body-md text-on-surface leading-relaxed">
              {insight.body.map((seg, i) =>
                seg.highlight ? (
                  <span key={i} className="text-primary font-semibold">
                    {seg.text}
                  </span>
                ) : (
                  <span key={i}>{seg.text}</span>
                ),
              )}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Gradient variant: gradient border with header label
  return (
    <section className="relative p-[1px] rounded-xl bg-gradient-to-br from-ai-narrative-tint/60 via-surface-elevated to-primary/30 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
      <div className="bg-surface-elevated/90 backdrop-blur-xl rounded-xl p-5 flex flex-col gap-3">
        {showLabel && (
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined icon-fill text-ai-narrative-tint animate-pulse">
              auto_awesome
            </span>
            <span className="font-label-caps text-label-caps text-secondary font-bold uppercase tracking-wider">
              {label}
            </span>
          </div>
        )}
        <p className="font-body-lg text-body-lg text-on-surface leading-relaxed">
          {insight.body.map((seg, i) =>
            seg.highlight ? (
              <span key={i} className="text-primary font-semibold">
                {seg.text}
              </span>
            ) : (
              <span key={i}>{seg.text}</span>
            ),
          )}
        </p>
      </div>
    </section>
  );
}
