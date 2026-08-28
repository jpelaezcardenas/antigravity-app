"use client";

import { useEffect, useState } from "react";
import { formatCop } from "@/lib/format";
import {
  fetchLiquidityBridge,
  type LiquidityBridgeSnapshot,
} from "@/lib/api-client";

type CardStatus = "loading" | "ready" | "unavailable" | "not_in_plan";

export function MonthlyLiquidityBridgeCard() {
  const [bridge, setBridge] = useState<LiquidityBridgeSnapshot | null>(null);
  const [status, setStatus] = useState<CardStatus>("loading");

  useEffect(() => {
    let cancelled = false;

    fetchLiquidityBridge()
      .then((snapshot) => {
        if (cancelled) return;
        if (snapshot.status === "empty") {
          setStatus("unavailable");
          return;
        }
        // plan-tier-feature-gating: distinct from "unavailable" — that means "we tried,
        // no data"; this means "this feature isn't in your plan" (design.md D4).
        if (snapshot.status === "not_in_plan") {
          setStatus("not_in_plan");
          return;
        }
        setBridge(snapshot);
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        // Never fall back to flujoDetalleMock.liquidityBridge on error — data-bound
        // cards must render an honest unavailable state (spec `client-pwa-live-data`,
        // scenario "Unavailable state renders honestly, never a mock value").
        console.warn("[MonthlyLiquidityBridgeCard] liquidity bridge fetch failed", error);
        setStatus("unavailable");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <section className="bg-surface-elevated border border-white/5 rounded-xl p-6 flex flex-col gap-4 animate-pulse">
        <h3 className="font-label-caps text-label-caps text-primary-container uppercase tracking-wider mb-2">
          Puente de Liquidez (Mensual)
        </h3>
        <div className="flex flex-col gap-3">
          <div className="h-9 w-full bg-white/10 rounded" />
          <div className="h-9 w-full bg-white/10 rounded" />
          <div className="h-9 w-full bg-white/10 rounded" />
          <div className="h-9 w-full bg-white/10 rounded" />
        </div>
      </section>
    );
  }

  if (status === "not_in_plan") {
    return (
      <section className="bg-surface-elevated border border-white/5 rounded-xl p-6 flex flex-col gap-4">
        <h3 className="font-label-caps text-label-caps text-primary-container uppercase tracking-wider mb-2">
          Puente de Liquidez (Mensual)
        </h3>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Esta función no está incluida en tu plan.
        </p>
      </section>
    );
  }

  if (status === "unavailable" || !bridge) {
    return (
      <section className="bg-surface-elevated border border-white/5 rounded-xl p-6 flex flex-col gap-4">
        <h3 className="font-label-caps text-label-caps text-primary-container uppercase tracking-wider mb-2">
          Puente de Liquidez (Mensual)
        </h3>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Datos no disponibles por el momento.
        </p>
      </section>
    );
  }

  return (
    <section className="bg-surface-elevated border border-white/5 rounded-xl p-6 flex flex-col gap-4">
      <h3 className="font-label-caps text-label-caps text-primary-container uppercase tracking-wider mb-2">
        Puente de Liquidez (Mensual)
      </h3>
      <div className="flex flex-col gap-3 font-data-mono text-data-mono">
        <div className="flex justify-between items-center py-2 border-b border-surface-variant">
          <span className="text-on-surface-variant font-body-md text-body-md">
            Saldo Inicial
          </span>
          <span className="text-on-surface">
            {formatCop(bridge.initial_balance / 100)}
          </span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-surface-variant">
          <span className="text-on-surface-variant font-body-md text-body-md">
            Ingresos
          </span>
          <span className="text-status-success">
            + {formatCop(bridge.inflows / 100)}
          </span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-surface-variant">
          <span className="text-on-surface-variant font-body-md text-body-md">
            Egresos
          </span>
          <span className="text-status-critical">
            {formatCop(-(bridge.outflows / 100))}
          </span>
        </div>
        <div className="flex justify-between items-center pt-2 mt-1">
          <span className="text-on-surface font-title-md text-title-md">
            Saldo Final
          </span>
          <span className="text-primary font-title-md text-title-md">
            {formatCop(bridge.final_balance / 100)}
          </span>
        </div>
      </div>
    </section>
  );
}
