"use client";

import { useEffect, useState } from "react";
import { formatCop } from "@/lib/format";
import {
  fetchFinancials,
  fetchTenantMe,
  fetchCentinelaAlerts,
  type FinancialsSnapshot,
  type TenantMeSnapshot,
} from "@/lib/api-client";

type Status = "loading" | "ready" | "empty" | "error";

/**
 * Visual pilot for PWA V2 (Fase 3) — same data contracts as CashTodayCard/
 * ActiveAlerts (fetchFinancials/fetchCentinelaAlerts/fetchTenantMe), new
 * "hero" composition (Google Weather-inspired: dominant figure, minimal
 * negative space, pill status badge). Never fabricates an insight sentence
 * or a last-updated timestamp the backend doesn't return — see the two
 * items Stitch's mockup showed that were dropped here for that reason.
 */
export function PulsoHeroV2() {
  const [status, setStatus] = useState<Status>("loading");
  const [cashTotal, setCashTotal] = useState<number | null>(null);
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);
  const [alertCount, setAlertCount] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([fetchFinancials(), fetchTenantMe(), fetchCentinelaAlerts()]).then(
      ([financialsResult, tenantResult, alertsResult]) => {
        if (cancelled) return;

        if (financialsResult.status === "fulfilled") {
          const snapshot: FinancialsSnapshot = financialsResult.value;
          if (snapshot.status === "empty") {
            setStatus("empty");
          } else {
            setCashTotal(snapshot.caja_real / 100);
            setStatus("ready");
          }
        } else {
          console.warn("[PulsoHeroV2] financials fetch failed", financialsResult.reason);
          setStatus("error");
        }

        if (tenantResult.status === "fulfilled") {
          setTenant(tenantResult.value);
        }

        if (alertsResult.status === "fulfilled" && alertsResult.value.status !== "not_in_plan") {
          setAlertCount(alertsResult.value.alerts.length);
        }
      },
    );

    return () => {
      cancelled = true;
    };
  }, []);

  const tenantLabel = tenant?.legal_name ?? "Tu negocio";

  return (
    <div className="relative pt-2">
      {/* Halo turquesa contenido, señal independiente del dominio "caja" — DESIGN_SYSTEM.md §2 */}
      <div
        aria-hidden
        className="absolute -top-10 -left-6 w-80 h-56 bg-primary/15 rounded-full blur-3xl pointer-events-none -z-0"
      />

      <div className="relative z-10 flex flex-col gap-1.5">
        <div className="text-xs font-medium tracking-wide text-on-surface-variant/90">
          {tenantLabel}
        </div>

        {status === "loading" && (
          <div className="h-16 w-56 bg-white/10 rounded animate-pulse" />
        )}

        {status === "error" && (
          <p className="font-body-md text-body-md text-on-surface-variant">
            No pudimos actualizar tu Caja Real. Intenta de nuevo en un momento.
          </p>
        )}

        {status === "empty" && (
          <p className="font-body-md text-body-md text-on-surface-variant">
            Sin datos aún. Ingresa tus movimientos para ver tu caja real.
          </p>
        )}

        {status === "ready" && cashTotal !== null && (
          <>
            <div className="inline-flex items-baseline font-extralight tracking-tight text-white tabular-nums leading-none text-[56px] sm:text-[68px]">
              {formatCop(cashTotal)}
            </div>
            <p className="text-on-surface-variant text-sm font-normal">Saldo bancario</p>
            {alertCount > 0 && (
              <div className="mt-1">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container/60 border border-outline-variant/40 backdrop-blur-md">
                  <span className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse" />
                  <span className="text-xs font-normal text-on-surface-variant tracking-wide">
                    {alertCount} {alertCount === 1 ? "alerta activa" : "alertas activas"}
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
