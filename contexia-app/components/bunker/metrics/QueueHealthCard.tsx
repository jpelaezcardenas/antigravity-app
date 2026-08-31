"use client";

import { useEffect, useState } from "react";
import { fetchQueueHealth, type QueueHealth } from "@/lib/metrics-client";

function minutesLabel(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

export function QueueHealthCard() {
  const [data, setData] = useState<QueueHealth | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchQueueHealth()
      .then((d) => { setData(d); setStatus("ready"); })
      .catch(() => setStatus("error"));
  }, []);

  const pendingTone =
    data === null
      ? ""
      : data.pending === 0
        ? "text-status-success"
        : data.pending < 10
          ? "text-on-surface"
          : "text-status-warning";

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        Salud de la Cola
      </span>

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
            <span className={`text-3xl font-bold tabular-nums ${pendingTone}`}>
              {data.pending}
            </span>
            <span className="text-xs text-on-surface-variant mb-1">pendientes de revisión</span>
          </div>

          <div className="bg-surface-container rounded-lg px-3 py-2.5 flex items-center justify-between">
            <span className="text-[10px] text-on-surface-variant uppercase tracking-wide">Tiempo promedio revisión</span>
            <span className="text-base font-bold text-on-surface">
              {minutesLabel(data.avg_review_seconds)}
            </span>
          </div>

          <div className="flex items-center gap-1.5 mt-1">
            <span
              className={`w-2 h-2 rounded-full ${
                data.pending === 0
                  ? "bg-status-success"
                  : data.pending < 10
                    ? "bg-status-warning"
                    : "bg-status-error"
              }`}
            />
            <span className="text-xs text-on-surface-variant">
              {data.pending === 0
                ? "Cola vacía — todo aprobado"
                : data.pending < 10
                  ? "Cola normal"
                  : "Cola acumulada — revisar"}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
