"use client";

import { useEffect, useState } from "react";

interface CronJob {
  id: string;
  name: string;
  schedule: string;
  last_run?: Date;
  next_run?: Date;
  status: "success" | "failed" | "pending";
}

const MOCK_CRON_JOBS: CronJob[] = [
  {
    id: "jarvis-morning-brief",
    name: "Jarvis — Brief Matutino",
    schedule: "0 9 * * *",
    last_run: new Date(Date.now() - 2 * 60 * 60 * 1000),
    next_run: new Date(Date.now() + 22 * 60 * 60 * 1000),
    status: "success",
  },
  {
    id: "centinela-scan",
    name: "Centinela — Escaneo Fiscal",
    schedule: "0 8,14,20 * * *",
    last_run: new Date(Date.now() - 1 * 60 * 60 * 1000),
    next_run: new Date(Date.now() + 6 * 60 * 60 * 1000),
    status: "success",
  },
  {
    id: "radar-daily",
    name: "Radar — Análisis Diario",
    schedule: "0 22 * * *",
    last_run: new Date(Date.now() - 26 * 60 * 60 * 1000),
    next_run: new Date(Date.now() + 20 * 60 * 60 * 1000),
    status: "success",
  },
];

export function CronJobsMonitor() {
  const [jobs, setJobs] = useState<CronJob[]>([]);

  useEffect(() => {
    setJobs(MOCK_CRON_JOBS);
  }, []);

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        Tareas Programadas
      </span>

      <div className="flex flex-col gap-2">
        {jobs.map((job) => (
          <div key={job.id} className="flex items-start gap-3 pb-2 border-b border-outline-variant/20 last:border-b-0">
            <div className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${
              job.status === "success"
                ? "bg-status-success"
                : job.status === "failed"
                  ? "bg-status-error"
                  : "bg-status-warning"
            }`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-on-surface truncate">
                {job.name}
              </p>
              <p className="text-xs text-on-surface-variant">
                {job.schedule}
              </p>
              {job.next_run && (
                <p className="text-xs text-on-surface-variant mt-1">
                  Próxima: {formatTimeUntil(job.next_run)}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTimeUntil(date: Date): string {
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) return `en ${hours}h ${minutes}m`;
  return `en ${minutes}m`;
}
