"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { CashToday } from "@/lib/types/contexia";
import { formatCop } from "@/lib/format";
import { fetchFinancials, type FinancialsSnapshot } from "@/lib/api-client";
import { pulsoMock } from "@/lib/mock/pulso";

const DETAIL_HREF = "/app/flujo-detalle";

function toCashToday(snapshot: FinancialsSnapshot): CashToday {
  // Backend returns COP minor units (cents); the real screens/formatCop work in
  // whole COP, matching the existing pulsoMock convention (e.g. 42_850_000).
  return {
    total: snapshot.caja_real / 100,
    yours: snapshot.dinero_disponible / 100,
    yesterdaySales: snapshot.ventas_ayer / 100,
    expenses: snapshot.gastos_ayer / 100,
    detailHref: DETAIL_HREF,
  };
}

export function CashTodayCard() {
  const [cash, setCash] = useState<CashToday | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "empty">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchFinancials()
      .then((snapshot) => {
        if (cancelled) return;
        if (snapshot.status === "empty") {
          setStatus("empty");
          return;
        }
        setCash(toCashToday(snapshot));
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        // Spec "degrades gracefully": on any fetch failure fall back to the
        // baked-in placeholder figures — the end user must never see an error
        // banner here (same fail-safe contract as the retired injected script).
        console.warn("[CashTodayCard] financials fetch failed, using fallback", error);
        setCash(pulsoMock.cash);
        setStatus("ready");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] relative overflow-hidden animate-pulse">
        <h2 className="font-body-md text-body-md text-white mb-2">
          Caja Real de Hoy
        </h2>
        <div className="h-9 w-48 bg-white/10 rounded mb-1" />
        <div className="h-5 w-64 bg-white/10 rounded mt-2" />
      </section>
    );
  }

  if (status === "empty" || !cash) {
    return (
      <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 relative overflow-hidden">
        <h2 className="font-body-md text-body-md text-white mb-2">
          Caja Real de Hoy
        </h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Sin datos aún. Ingresa tus movimientos para ver tu caja real.
        </p>
      </section>
    );
  }

  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] relative overflow-hidden">
      <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-primary/10 to-transparent pointer-events-none" />

      <div className="relative z-10">
        <h2 className="font-body-md text-body-md text-white mb-2">
          Caja Real de Hoy
        </h2>
        <div className="font-headline-xl text-headline-xl text-primary mb-1 tracking-tight">
          {formatCop(cash.total)}
        </div>
        <p className="font-body-md text-body-md text-on-surface mb-6">
          Dinero tuyo de verdad: {formatCop(cash.yours)}
        </p>

        <div className="flex flex-col gap-2 border-t border-outline-variant/30 pt-4">
          <div className="flex justify-between items-center">
            <span className="font-data-mono text-data-mono text-on-surface-variant">
              Ventas de ayer:
            </span>
            <span className="font-data-mono text-data-mono text-on-surface">
              {formatCop(cash.yesterdaySales)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-data-mono text-data-mono text-on-surface-variant">
              Salidas de plata:
            </span>
            <span className="font-data-mono text-data-mono text-on-surface">
              {formatCop(cash.expenses)}
            </span>
          </div>
        </div>

        {cash.detailHref && (
          <Link
            href={cash.detailHref}
            className="mt-6 w-full flex items-center justify-center gap-2 py-2 border border-primary-container/20 rounded-lg text-white hover:bg-primary-container/10 transition-all active:scale-[0.98]"
          >
            <span className="font-label-caps text-label-caps">
              Ver de dónde viene tu plata
            </span>
            <span className="material-symbols-outlined text-sm">
              chevron_right
            </span>
          </Link>
        )}
      </div>
    </section>
  );
}
