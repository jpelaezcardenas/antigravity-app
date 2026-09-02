"use client";

import { useEffect, useState } from "react";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";
import { HermesStatusCard } from "./HermesStatusCard";
import { JarvisChatInterface } from "./JarvisChatInterface";
import { CronJobsMonitor } from "./CronJobsMonitor";

type LoadState = "loading" | "ready" | "empty";

function readRoleFromJwt(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie
    .split("; ")
    .find((c) => c.startsWith("sb-access-token="));
  if (!match) return "";
  const token = match.split("=").slice(1).join("=");
  const parts = token.split(".");
  if (parts.length !== 3) return "";
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
    const appMeta = payload.app_metadata ?? {};
    const userMeta = payload.user_metadata ?? {};
    return String(
      appMeta.role ?? appMeta.account_role ?? userMeta.role ?? userMeta.account_role ?? ""
    ).toLowerCase();
  } catch {
    return "";
  }
}

function JarvisLockedState({ tier }: { tier: string | null }) {
  const msg =
    tier === "freemium" || tier === "starter"
      ? "Disponible desde el plan GPS Financiero. Habla con tu asesor para actualizar."
      : "Disponible en el plan Contexia Total.";

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
      <span className="material-symbols-outlined text-primary text-[48px]">lock</span>
      <p className="text-white font-semibold text-base">Jarvis no disponible en tu plan</p>
      <p className="text-on-surface-variant text-sm max-w-xs">{msg}</p>
    </div>
  );
}

export function AgenticOsSection() {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const role = readRoleFromJwt();
    setIsAdmin(["admin", "superadmin", "contexia_admin"].includes(role));

    let cancelled = false;
    fetchTenantMe()
      .then((snapshot) => {
        if (cancelled) return;
        setTenant(snapshot);
        setLoadState("ready");
      })
      .catch(() => {
        if (cancelled) return;
        setLoadState("empty");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tier = tenant?.plan_tier ?? null;
  const hasJarvisChat = isAdmin || tier === "growth" || tier === "enterprise";
  const hasVoice = isAdmin || tier === "enterprise";

  return (
    <div className="flex flex-col gap-6">
      {/* Section header */}
      <div className="flex items-center gap-2">
        <span className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wide whitespace-nowrap">
          Agentic OS · Hermes
        </span>
        <div className="flex-1 h-px bg-outline-variant/30" />
        <span className="text-[10px] text-on-surface-variant">
          Powered by Hermes · Torre Tauret
        </span>
      </div>

      {/* Loading skeleton */}
      {loadState === "loading" && (
        <div className="flex flex-col gap-4">
          <div className="h-12 bg-white/5 rounded-xl animate-pulse" />
          <div className="h-[420px] bg-white/5 rounded-xl animate-pulse" />
        </div>
      )}

      {/* Content */}
      {loadState !== "loading" && (
        <div className="flex flex-col gap-4">
          {/* Hermes status — always visible */}
          <HermesStatusCard />

          {/* Admin-only: cron monitor */}
          {isAdmin && <CronJobsMonitor />}

          {/* Feature-gated chat */}
          {hasJarvisChat ? (
            <JarvisChatInterface withVoice={hasVoice} />
          ) : (
            <JarvisLockedState tier={tier} />
          )}
        </div>
      )}
    </div>
  );
}
