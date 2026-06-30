import type { CashProjection, ProjectionTone } from "@/lib/types/contexia";
import { CARD_SHADOW } from "@/lib/styles/cardStyles";

const TONE_STYLES: Record<
  ProjectionTone,
  {
    stroke: string;
    gradient: string;
    glow: string;
    headerIcon: string;
    headerIconColor: string;
  }
> = {
  warning: {
    stroke: "#F59E0B",
    gradient: "from-status-warning/20",
    glow: "drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]",
    headerIcon: "trending_down",
    headerIconColor: "text-status-warning",
  },
  base: {
    stroke: "#2DD4BF",
    gradient: "from-primary/20",
    glow: "drop-shadow-[0_0_8px_rgba(45,212,191,0.5)]",
    headerIcon: "trending_up",
    headerIconColor: "text-status-success",
  },
  positive: {
    stroke: "#57f1db",
    gradient: "from-primary/30",
    glow: "drop-shadow-[0_0_12px_rgba(87,241,219,0.6)]",
    headerIcon: "trending_up",
    headerIconColor: "text-status-success",
  },
};

export function CashProjectionCard({
  projection,
}: {
  projection: CashProjection;
}) {
  const tone = TONE_STYLES[projection.tone];

  return (
    <section className={`bg-surface-elevated rounded-xl border border-white/10 p-5 flex flex-col gap-4 ${CARD_SHADOW.base}`}>
      <div className="flex justify-between items-end">
        <div>
          <h3 className="font-title-md text-title-md text-primary-container">
            Flujo de Caja Proyectado
          </h3>
          <p className="font-data-mono text-data-mono text-on-surface-variant mt-1">
            vs. Obligaciones Críticas
          </p>
        </div>
        <span className={`material-symbols-outlined ${tone.headerIconColor}`}>
          {tone.headerIcon}
        </span>
      </div>

      <div className="h-[180px] w-full relative mt-2 border-b border-l border-outline-variant/30 flex items-end">
        {/* Grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="w-full h-px bg-outline-variant/10" />
          ))}
        </div>

        {/* Area gradient under the curve */}
        <div
          className={`absolute bottom-0 left-0 right-0 h-[70%] bg-gradient-to-t to-transparent blur-[2px] ${tone.gradient}`}
        />

        {/* The curve itself */}
        <svg
          className={`absolute inset-0 w-full h-full ${tone.glow}`}
          preserveAspectRatio="none"
          viewBox="0 0 100 100"
          aria-hidden
        >
          <path
            d={projection.pathD}
            fill="none"
            stroke={tone.stroke}
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
        </svg>

        {/* Obligation deadline marker (e.g. IVA) */}
        <div
          className="absolute h-full w-px bg-status-critical/50 border-r border-dashed border-status-critical/50"
          style={{ left: `${projection.obligation.positionPct}%`, bottom: 0 }}
        >
          <div className="absolute -top-6 -translate-x-1/2 bg-surface border border-status-critical/30 rounded px-2 py-0.5 font-label-caps text-label-caps text-status-critical">
            {projection.obligation.label}
          </div>
          <div
            className="absolute -translate-x-1/2 w-2 h-2 rounded-full bg-status-critical shadow-[0_0_8px_rgba(239,68,68,0.8)]"
            style={{ top: `${projection.obligation.pointTopPct}%` }}
          />
        </div>

        {/* X-axis labels */}
        <div className="absolute -bottom-6 w-full flex justify-between font-label-caps text-label-caps text-on-surface-variant/60">
          {projection.axisLabels.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
      </div>
    </section>
  );
}
