"use client";

import { useEffect, useState } from "react";
import { fetchTopVendors, type VendorEntry } from "@/lib/metrics-client";

export function TopVendorsCard() {
  const [vendors, setVendors] = useState<VendorEntry[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchTopVendors(10)
      .then((d) => { setVendors(d); setStatus("ready"); })
      .catch(() => setStatus("error"));
  }, []);

  const max = vendors.length > 0 ? vendors[0].count : 1;

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        Top Proveedores
      </span>

      {status === "loading" && (
        <div className="h-16 flex items-center justify-center">
          <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>
      )}

      {status === "error" && (
        <p className="text-xs text-on-surface-variant">Sin datos disponibles</p>
      )}

      {status === "ready" && vendors.length === 0 && (
        <p className="text-xs text-on-surface-variant">Sin transacciones registradas aún</p>
      )}

      {status === "ready" && vendors.length > 0 && (
        <div className="flex flex-col gap-2.5">
          {vendors.map((v, i) => {
            const pct = Math.round((v.count / max) * 100);
            return (
              <div key={v.vendor} className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-on-surface-variant w-4 shrink-0 text-right">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs text-on-surface truncate max-w-[160px]">{v.vendor}</span>
                    <span className="text-xs font-mono text-on-surface-variant ml-2 shrink-0">{v.count}</span>
                  </div>
                  <div className="h-1 bg-surface-container-high rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary/60 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
