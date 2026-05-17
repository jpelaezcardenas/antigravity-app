import type { UpcomingMilestone, AlertSeverity } from "@/lib/types/contexia";
import { formatCop } from "@/lib/format";

const SEVERITY_COLOR: Record<AlertSeverity, string> = {
  warning: "text-status-warning",
  critical: "text-status-critical",
};

export function UpcomingMilestonesCard({
  milestones,
}: {
  milestones: UpcomingMilestone[];
}) {
  return (
    <section className="flex flex-col gap-4">
      <h3 className="font-title-md text-title-md text-primary-container border-b border-white/5 pb-2">
        Próximos Hitos
      </h3>
      <div className="flex flex-col gap-3">
        {milestones.map((m) => (
          <div
            key={m.id}
            className="bg-surface-container border border-outline-variant/20 rounded-lg p-4 flex items-center gap-4 hover:border-primary/30 transition-colors"
          >
            <div className="flex flex-col items-center justify-center bg-surface w-12 h-12 rounded border border-white/5 shrink-0">
              <span
                className={`font-label-caps text-label-caps ${SEVERITY_COLOR[m.severity]}`}
              >
                {m.monthAbbr}
              </span>
              <span className="font-title-md text-title-md font-bold">
                {m.day}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-body-md text-body-md font-semibold text-on-surface truncate">
                {m.title}
              </h4>
              <p className="font-label-caps text-label-caps text-on-surface-variant truncate">
                {m.subtitle}
              </p>
            </div>
            <div className="font-data-mono text-data-mono text-on-surface text-right shrink-0">
              {formatCop(m.amount)}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
