"use client";

import { useEffect, useState } from "react";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";

type PlanTier = "freemium" | "starter" | "growth" | "enterprise";

/**
 * PWA V2 (Fase 5) — replaces the generic "lock" treatment with the explicit
 * access-state vocabulary from PREMIUM_AND_ENTITLEMENTS.md §4: distinguishing
 * "no_incluido" (not in this plan) from a hypothetical "aun_no_construido" or
 * "no_disponible_temporalmente" instead of collapsing every gated case into
 * one padlock icon. Mirrors PLAN_FEATURES in apps/backend/core/plan_features.py
 * exactly (jarvis_chat from growth, jarvis_voice from enterprise only) — no
 * capabilities endpoint exists, so this stays inline like the V1 banner did;
 * NOT a new API contract. `plan_features.has_feature()` itself is untouched,
 * per the founder's D05 decision — this is presentation only.
 */
const FEATURE_GATE: Record<
  PlanTier,
  { feature: string; state: "no_incluido"; requiredTierLabel: string }[]
> = {
  freemium: [
    { feature: "JARVIS — chat con tu asistente", state: "no_incluido", requiredTierLabel: "Contexia Pro" },
  ],
  starter: [
    { feature: "JARVIS — chat con tu asistente", state: "no_incluido", requiredTierLabel: "Contexia Pro" },
  ],
  growth: [
    { feature: "JARVIS — comandos por voz", state: "no_incluido", requiredTierLabel: "Contexia Total" },
  ],
  enterprise: [],
};

const STATE_LABEL: Record<string, string> = {
  no_incluido: "No incluido en tu plan",
};

/**
 * Shown when the resolved tenant's plan has a gated feature not yet included.
 * Never renders a fake "loading" skeleton or a generic error banner — same
 * honesty rules as UpgradePlanBanner.tsx (nothing while loading/on fetch error).
 */
export function UpgradePlanBannerV2() {
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchTenantMe()
      .then((snapshot) => {
        if (cancelled) return;
        setTenant(snapshot);
      })
      .catch((error) => {
        if (cancelled) return;
        console.warn("[UpgradePlanBannerV2] tenant/me fetch failed", error);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (!tenant || !tenant.plan_tier) return null;

  const gates = FEATURE_GATE[tenant.plan_tier as PlanTier];
  if (!gates || gates.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      {gates.map((gate) => (
        <section
          key={gate.feature}
          className="rounded-2xl border border-outline-variant/40 bg-surface-container/60 backdrop-blur-md p-4 flex items-start gap-3"
        >
          <span className="material-symbols-outlined text-on-surface-variant text-[20px] mt-0.5">
            lock_clock
          </span>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-0.5">
              <p className="text-sm text-white font-semibold">{gate.feature}</p>
              <span className="text-[9px] font-medium tracking-wide uppercase px-1.5 py-0.5 rounded bg-outline-variant/20 text-on-surface-variant">
                {STATE_LABEL[gate.state]}
              </span>
            </div>
            <p className="text-xs text-on-surface-variant">
              Disponible desde {gate.requiredTierLabel}. Habla con tu asesor para actualizar tu
              plan.
            </p>
          </div>
        </section>
      ))}
    </div>
  );
}
