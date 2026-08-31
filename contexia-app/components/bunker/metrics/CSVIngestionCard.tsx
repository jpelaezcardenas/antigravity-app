"use client";

import { useEffect, useState } from "react";
import { fetchCSVIngestionMetrics, type CSVIngestionMetrics } from "@/lib/metrics-client";

export function CSVIngestionCard() {
  const [data, setData] = useState<CSVIngestionMetrics | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchCSVIngestionMetrics(7)
      .then((d) => { setData(d); setStatus("ready"); })
      .catch(() => setStatus("error"));
  }, []);

  const errorRate =
    data && data.rows_processed > 0
      ? ((data.rows_error / data.rows_processed) * 100).toFixed(1)
      : "0.0";

  const errorTone =
    data && parseFloat(errorRate) > 5
      ? "text-status-error"
      : data && parseFloat(errorRate) > 1
        ? "text-status-warning"
        : "text-status-success";

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
          Ingesta CSV · 7 días
        </span>
        {status === "ready" && data && (
          <span className={`text-[10px] font-bold ${errorTone}`}>
            {errorRate}% errores
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
              {data.batches}
            </span>
            <span className="text-xs text-on-surface-variant mb-1">archivos procesados</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="bg-surface-container rounded-lg px-3 py-2">
              <div className="text-[10px] text-on-surface-variant uppercase tracking-wide">Filas OK</div>
              <div className="text-base font-bold text-status-success mt-0.5">
                {data.rows_processed.toLocaleString("es-CO")}
              </div>
            </div>
            <div className="bg-surface-container rounded-lg px-3 py-2">
              <div className="text-[10px] text-on-surface-variant uppercase tracking-wide">Filas con error</div>
              <div className={`text-base font-bold mt-0.5 ${parseFloat(errorRate) > 1 ? "text-status-warning" : "text-on-surface-variant"}`}>
                {data.rows_error.toLocaleString("es-CO")}
              </div>
            </div>
          </div>

          {data.daily.length > 0 && (
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-on-surface-variant uppercase tracking-wide">Por día</span>
              {data.daily.slice().reverse().map((d) => {
                const dayErrorRate = d.rows_ok > 0 ? (d.rows_err / d.rows_ok) * 100 : 0;
                return (
                  <div key={d.date} className="flex items-center justify-between text-xs text-on-surface-variant">
                    <span className="w-20 shrink-0">
                      {new Date(d.date + "T12:00:00").toLocaleDateString("es-CO", { weekday: "short", day: "numeric" })}
                    </span>
                    <span>{d.batches} lotes</span>
                    <span>{d.rows_ok.toLocaleString("es-CO")} filas</span>
                    <span className={dayErrorRate > 2 ? "text-status-warning" : "text-on-surface-variant"}>
                      {d.rows_err} err
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
