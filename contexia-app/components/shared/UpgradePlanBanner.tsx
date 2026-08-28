"use client";

import { useEffect, useState } from "react";
import { fetchTenantMe } from "@/lib/api-client";

/**
 * Shown only when the resolved tenant's plan_tier is "freemium" (plan-tier-feature-gating).
 * Purely presentational — the screen it sits on stays 100% mock either way; this banner
 * does not claim or imply the underlying screen has real data (proposal.md, task 9.1).
 * Renders nothing while loading or on any fetch failure/non-freemium tier — never a
 * layout-shifting skeleton for what is, for most tenants, a permanently absent banner.
 */
export function UpgradePlanBanner() {
  const [isFreemium, setIsFreemium] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetchTenantMe()
      .then((snapshot) => {
        if (cancelled) return;
        setIsFreemium(snapshot.plan_tier === "freemium");
      })
      .catch((error) => {
        if (cancelled) return;
        console.warn("[UpgradePlanBanner] tenant/me fetch failed", error);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (!isFreemium) return null;

  return (
    <section className="bg-primary/10 border border-primary/30 rounded-xl p-4 flex items-center gap-3">
      <span className="material-symbols-outlined text-primary">lock</span>
      <div className="flex-1">
        <p className="font-body-md text-body-md text-white font-semibold">
          Actualiza tu plan para desbloquear esta función
        </p>
        <p className="font-body-md text-[12px] text-on-surface-variant">
          Tu plan Freemium incluye Pulso Diario. Habla con tu asesor para ver el resto.
        </p>
      </div>
    </section>
  );
}
