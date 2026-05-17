import type { FiscalRiskStatus, RiskLevel } from "@/lib/types/contexia";

const RISK_STYLES: Record<
  RiskLevel,
  { iconColor: string; backdropColor: string; glowColor: string }
> = {
  bajo: {
    iconColor: "text-status-success",
    backdropColor: "bg-status-success/5",
    glowColor: "bg-status-success/20",
  },
  medio: {
    iconColor: "text-status-warning",
    backdropColor: "bg-status-warning/5",
    glowColor: "bg-status-warning/20",
  },
  alto: {
    iconColor: "text-status-critical",
    backdropColor: "bg-status-critical/5",
    glowColor: "bg-status-critical/20",
  },
};

export function FiscalRiskStatusCard({
  status,
}: {
  status: FiscalRiskStatus;
}) {
  const styles = RISK_STYLES[status.level];
  return (
    <section className="relative bg-surface-elevated rounded-xl p-6 border border-white/10 overflow-hidden flex flex-col items-center justify-center text-center">
      <div
        className={`absolute inset-0 backdrop-blur-[12px] z-0 ${styles.backdropColor}`}
      />
      <div
        className={`absolute w-32 h-32 rounded-full blur-[40px] z-0 ${styles.glowColor}`}
      />
      <div className="relative z-10 flex flex-col items-center gap-4">
        <span
          className={`material-symbols-outlined icon-fill text-[48px] ${styles.iconColor}`}
        >
          shield_locked
        </span>
        <div>
          <p className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider mb-1">
            {status.sectionLabel}
          </p>
          <h2 className="font-title-md text-title-md text-primary-container">
            {status.levelLabel}
          </h2>
        </div>
      </div>
    </section>
  );
}
