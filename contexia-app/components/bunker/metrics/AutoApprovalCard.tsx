"use client";

import { useEffect, useState } from "react";
import { fetchAutoApprovalMetrics, type AutoApprovalMetrics } from "@/lib/metrics-client";

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex-1 h-1.5 bg-surface-container-high rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-on-surface-variant w-6 text-right font-mono">{value}</span>
    </div>
  );
}

export function AutoApprovalCard() {
  const [data, setData] = useState<AutoApprovalMetrics | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchAutoApprovalMetrics(7)
      .then((d) => { setData(d); setStatus("ready"); })
      .catch(() => setStatus("error"));
  }, []);

  const fpRate =
    data && data.total_auto_approved > 0
      ? ((data.false_positives / data.total_auto_approved) * 100).toFixed(1)
      : "0.0";

  const maxDaily = data ? Math.max(...data.daily.map((d) => d.approved), 1) : 1;

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
          Auto-Aprobación · 7 días
        </span>
        {status === "ready" && (
          <span className="text-[10px] font-bold text-status-success bg-status-success/10 border border-status-success/25 rounded-full px-2 py-0.5">
            {fpRate}% falsos positivos
          </span>
        )}
      </div>

      {status === "loading" && (
        <div className="h-16 flex items-center justify-center">
          <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>
      )}

      {status === "error" && (
        <p className="text-xs text-on-surface-variant">Sin datos disponibles</p>
      )}

      {status === "ready" && data && (
        <>
          <div className="flex items-end gap-3">
            <span className="text-3xl font-bold text-on-surface tabular-nums">
              {data.total_auto_approved.toLocaleString("es-CO")}
            </span>
            <span className="text-xs text-on-surface-variant mb-1">transacciones aprobadas</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Recurrentes", value: data.by_rule.recurring, color: "bg-primary" },
              { label: "Vendors", value: data.by_rule.vendor, color: "bg-secondary" },
              { label: "Micro", value: data.by_rule.micro, color: "bg-tertiary" },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-surface-container rounded-lg px-3 py-2">
                <div className="text-[10px] text-on-surface-variant uppercase tracking-wide">{label}</div>
                <div className={`text-base font-bold mt-0.5 text-on-surface`}>{value}</div>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] text-on-surface-variant uppercase tracking-wide">Últimos 7 días</span>
            {data.daily.slice().reverse().map((d) => (
              <div key={d.date} className="flex items-center gap-2">
                <span className="text-[10px] text-on-surface-variant w-12 shrink-0">
                  {new Date(d.date + "T12:00:00").toLocaleDateString("es-CO", { weekday: "short", day: "numeric" })}
                </span>
                <div className="flex-1">
                  <MiniBar value={d.approved} max={maxDaily} color="bg-primary" />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
