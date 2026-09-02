"use client";

// Static list sourced from Hermes jobs.json — no live fetch for now (see design.md OQ4).
// Update this list when new cron jobs are registered in Hermes.
const CRON_JOBS = [
  { id: "pulso-diario", label: "Pulso Diario", schedule: "8:00 AM COT" },
  { id: "centinela-diario", label: "Centinela Fiscal", schedule: "8:05 AM COT" },
  { id: "radar-semanal", label: "Radar Predictivo", schedule: "Lunes 8:10 AM COT" },
  { id: "social-ops-mañana", label: "Social Content Plan", schedule: "7:00 AM COT" },
  { id: "auditoria-sombra", label: "Auditoría Sombra", schedule: "Domingo 9:00 AM COT" },
  { id: "hubspot-sync", label: "HubSpot Sync", schedule: "Cada 5 min" },
  { id: "hermes-multi-tenant", label: "Hermes Multi-tenant Cron", schedule: "Cada hora" },
  { id: "jarvis-morning-brief", label: "Jarvis Morning Brief", schedule: "9:00 AM COT" },
];

export function CronJobsMonitor() {
  return (
    <div className="bg-surface-elevated rounded-xl border border-outline-variant/20 p-4 flex flex-col gap-3">
      <p className="text-[11px] text-on-surface-variant uppercase tracking-widest font-bold">
        Cron Jobs · Hermes
      </p>
      <ul className="flex flex-col gap-1.5">
        {CRON_JOBS.map((job) => (
          <li key={job.id} className="flex items-center justify-between gap-2 text-sm">
            <span className="text-white/80 truncate">{job.label}</span>
            <span className="text-[11px] text-on-surface-variant whitespace-nowrap">
              {job.schedule}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
