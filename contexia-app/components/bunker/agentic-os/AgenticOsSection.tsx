"use client";

import { useEffect, useState } from "react";
import { hasFeature } from "@/lib/plan-features";
import { fetchTenantMe, type TenantMeSnapshot as Tenant } from "@/lib/api-client";
import { HermesStatusCard } from "./HermesStatusCard";
import { JarvisChatInterface } from "./JarvisChatInterface";
import { CronJobsMonitor } from "./CronJobsMonitor";
import { VoiceToggle } from "./VoiceToggle";

export function AgenticOsSection() {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [tenantStatus, setTenantStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchTenantMe()
      .then((t) => { setTenant(t); setTenantStatus("ready"); })
      .catch(() => setTenantStatus("error"));
  }, []);

  const canUseJarvis = tenant?.plan_tier && hasFeature(tenant.plan_tier as import("@/lib/plan-features").PlanTier, "jarvis_chat");
  const canUseVoice = tenant?.plan_tier && hasFeature(tenant.plan_tier as import("@/lib/plan-features").PlanTier, "jarvis_voice");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <span className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wide whitespace-nowrap">
          Agentic OS
        </span>
        <div className="flex-1 h-px bg-outline-variant/30" />
        <span className="text-[10px] text-on-surface-variant">
          Hermes Personal · Comandos por voz
        </span>
      </div>

      {tenantStatus === "error" && (
        <div className="bg-surface-container-low rounded-xl p-4 text-center text-on-surface-variant">
          No se pudo cargar la configuración de plan
        </div>
      )}

      {tenantStatus === "loading" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-surface-container-low rounded-xl p-4 h-32 animate-pulse" />
          <div className="bg-surface-container-low rounded-xl p-4 h-32 animate-pulse" />
        </div>
      )}

      {tenantStatus === "ready" && !canUseJarvis && (
        <div className="bg-surface-container-low rounded-xl p-6 text-center">
          <p className="text-on-surface font-medium mb-2">
            Jarvis está disponible en planes Growth y superior
          </p>
          <p className="text-on-surface-variant text-sm">
            Actualiza tu plan para acceder a esta funcionalidad
          </p>
        </div>
      )}

      {tenantStatus === "ready" && canUseJarvis && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1">
              <HermesStatusCard />
            </div>
            <div className="lg:col-span-2">
              <JarvisChatInterface />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CronJobsMonitor />
            {canUseVoice && <VoiceToggle />}
          </div>
        </>
      )}
    </div>
  );
}
