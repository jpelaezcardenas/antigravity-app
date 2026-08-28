"use client";

import { useEffect, useState } from "react";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";

const PLAN_TIER_LABEL: Record<string, string> = {
  freemium: "Plan Freemium",
  starter: "Plan Starter",
  growth: "Plan Growth",
  enterprise: "Plan Enterprise",
};

function toPlanLabel(planTier: string | null): string {
  if (!planTier) return "Plan";
  return PLAN_TIER_LABEL[planTier] ?? "Plan";
}

export function TenantInfoCard() {
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "empty">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchTenantMe()
      .then((snapshot) => {
        if (cancelled) return;
        if (snapshot.status === "empty" || !snapshot.legal_name) {
          setStatus("empty");
          return;
        }
        setTenant(snapshot);
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        // Never fall back to a mock company name/plan on error — same honest-degrade
        // rule as CashTodayCard/ActiveAlerts/MonthlyLiquidityBridgeCard.
        console.warn("[TenantInfoCard] tenant/me fetch failed", error);
        setStatus("empty");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const legalName = status === "ready" && tenant ? tenant.legal_name : "Mi Empresa";
  const planLabel =
    status === "ready" && tenant ? toPlanLabel(tenant.plan_tier) : "Plan";

  return (
    <section className="bg-surface-elevated rounded-xl border border-primary/20 p-5 flex items-center gap-4 shadow-[0_0_20px_rgba(45,212,191,0.08)]">
      <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-primary to-[#8B5CF6] flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(45,212,191,0.3)]">
        <span className="material-symbols-outlined text-white text-[28px]">
          store
        </span>
      </div>
      <div className="flex flex-col flex-1 min-w-0">
        {status === "loading" ? (
          <>
            <div className="h-5 w-32 bg-white/10 rounded animate-pulse mb-1" />
            <div className="h-3 w-24 bg-white/10 rounded animate-pulse" />
          </>
        ) : (
          <>
            <p className="font-title-md text-title-md text-white truncate">
              {legalName}
            </p>
            <p
              className="text-[10px] text-primary font-bold uppercase tracking-widest"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              {planLabel} · Activo
            </p>
          </>
        )}
      </div>
    </section>
  );
}
