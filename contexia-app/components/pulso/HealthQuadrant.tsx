import Link from "next/link";
import type { HealthKpi, StatusLevel } from "@/lib/types/contexia";

const STATUS_STYLES: Record<
  StatusLevel,
  { ring: string; text: string; halo: string; label: string }
> = {
  sana: {
    ring: "bg-status-success/20 border-status-success/30",
    text: "text-status-success",
    halo: "shadow-[0_0_15px_rgba(45,212,191,0.2)]",
    label: "Sana",
  },
  vigilancia: {
    ring: "bg-status-warning/20 border-status-warning/30",
    text: "text-status-warning",
    halo: "shadow-[0_0_15px_rgba(245,158,11,0.2)]",
    label: "En vigilancia",
  },
  alerta: {
    ring: "bg-status-critical/20 border-status-critical/30",
    text: "text-status-critical",
    halo: "shadow-[0_0_15px_rgba(239,68,68,0.2)]",
    label: "Crítica",
  },
};

function KpiTile({ kpi }: { kpi: HealthKpi }) {
  const styles = STATUS_STYLES[kpi.status];
  return (
    <div className="bg-surface-elevated rounded-xl p-4 border border-white/10 flex flex-col items-center text-center group">
      <div
        className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 border ${styles.ring} ${styles.halo}`}
      >
        <span className={`material-symbols-outlined ${styles.text}`}>
          {kpi.icon}
        </span>
      </div>
      <h3 className="font-label-caps text-label-caps text-primary-container mb-1 uppercase tracking-wider">
        {kpi.label}
      </h3>
      <span className={`font-body-md text-body-md font-medium ${styles.text}`}>
        {styles.label}
      </span>

      {kpi.detailHref && (
        <Link
          href={kpi.detailHref}
          className="mt-2 flex items-center justify-center text-on-surface-variant/60 group-hover:text-primary transition-colors"
        >
          <span className="material-symbols-outlined text-sm">
            chevron_right
          </span>
          <span className="text-[10px] uppercase font-bold ml-1">
            Ver detalle
          </span>
        </Link>
      )}
    </div>
  );
}

export function HealthQuadrant({ kpis }: { kpis: HealthKpi[] }) {
  return (
    <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {kpis.map((kpi) => (
        <KpiTile key={kpi.id} kpi={kpi} />
      ))}
    </section>
  );
}
