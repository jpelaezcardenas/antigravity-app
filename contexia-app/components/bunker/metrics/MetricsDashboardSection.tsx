"use client";

import { AutoApprovalCard } from "./AutoApprovalCard";
import { CSVIngestionCard } from "./CSVIngestionCard";
import { QueueHealthCard } from "./QueueHealthCard";
import { TopVendorsCard } from "./TopVendorsCard";

export function MetricsDashboardSection() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <span className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wide whitespace-nowrap">
          Métricas Operacionales
        </span>
        <div className="flex-1 h-px bg-outline-variant/30" />
        <span className="text-[10px] text-on-surface-variant">
          Actualizado a diario · datos de los últimos 7 días
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <AutoApprovalCard />
        <QueueHealthCard />
        <CSVIngestionCard />
        <TopVendorsCard />
      </div>
    </div>
  );
}
