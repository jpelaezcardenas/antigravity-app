"use client";

import { useEffect, useState } from "react";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";

type PlanTier = "freemium" | "starter" | "growth" | "enterprise";

interface BannerConfig {
  title: string;
  description: string;
  show: boolean;
}

const BANNER_CONFIG: Record<PlanTier, BannerConfig> = {
  freemium: {
    title: "Acceso a Jarvis — Tu asistente personal",
    description: "Disponible desde Contexia Pro. Habla con tu asesor para actualizar tu plan.",
    show: true,
  },
  starter: {
    title: "Acceso a Jarvis — Tu asistente personal",
    description: "Disponible desde Contexia Pro. Habla con tu asesor para actualizar tu plan.",
    show: true,
  },
  growth: {
    title: "Jarvis con voz — Comandos por audio",
    description: "Disponible en Contexia Total. Habla con tu asesor para acceder a esta función.",
    show: true,
  },
  enterprise: {
    title: "",
    description: "",
    show: false,
  },
};

/**
 * Shown when the resolved tenant's plan_tier is freemium, starter, or growth.
 * Displays tier-specific upgrade messaging for Jarvis features.
 * Renders nothing while loading or on any fetch failure — never a layout-shifting skeleton.
 */
export function UpgradePlanBanner() {
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
        console.warn("[UpgradePlanBanner] tenant/me fetch failed", error);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (!tenant || !tenant.plan_tier) return null;

  const config = BANNER_CONFIG[tenant.plan_tier as PlanTier];
  if (!config.show) return null;

  return (
    <section className="bg-primary/10 border border-primary/30 rounded-xl p-4 flex items-center gap-3">
      <span className="material-symbols-outlined text-primary">lock</span>
      <div className="flex-1">
        <p className="font-body-md text-body-md text-white font-semibold">
          {config.title}
        </p>
        <p className="font-body-md text-[12px] text-on-surface-variant">
          {config.description}
        </p>
      </div>
    </section>
  );
}
