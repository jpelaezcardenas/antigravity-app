"use client";

import { useEffect, useState } from "react";
import type { ActiveAlert, AlertSeverity } from "@/lib/types/contexia";
import { fetchCentinelaAlerts, type CentinelaAlert } from "@/lib/api-client";

const SEVERITY_ICON: Record<AlertSeverity, string> = {
  warning: "schedule",
  critical: "rule_folder",
};

const SEVERITY_ACCENT: Record<AlertSeverity, { border: string; iconBg: string; iconColor: string }> = {
  warning: {
    border: "border-l-warning",
    iconBg: "bg-warning/20",
    iconColor: "text-warning",
  },
  critical: {
    border: "border-l-status-critical",
    iconBg: "bg-status-critical/20",
    iconColor: "text-status-critical",
  },
};

function toSeverity(backendSeverity: string): AlertSeverity {
  return backendSeverity === "critical" ? "critical" : "warning";
}

function toActiveAlert(alert: CentinelaAlert, index: number): ActiveAlert {
  const severity = toSeverity(alert.severity);
  return {
    id: `${alert.rule_id || "alert"}-${index}`,
    icon: SEVERITY_ICON[severity],
    severity,
    message: alert.description ? `${alert.title} — ${alert.description}` : alert.title,
  };
}

/**
 * Visual pilot for PWA V2 (Fase 3) — same fetchCentinelaAlerts contract and
 * honesty rules as ActiveAlerts.tsx (never falls back to mock on error/empty),
 * restyled with left-border severity accents per DESIGN_SYSTEM.md.
 */
export function ActiveAlertsV2() {
  const [alerts, setAlerts] = useState<ActiveAlert[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "not_in_plan">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchCentinelaAlerts()
      .then((response) => {
        if (cancelled) return;
        if (response.status === "not_in_plan") {
          setAlerts([]);
          setStatus("not_in_plan");
          return;
        }
        setAlerts(response.alerts.map(toActiveAlert));
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        console.warn("[ActiveAlertsV2] centinela alerts fetch failed", error);
        setAlerts([]);
        setStatus("ready");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-2.5 animate-pulse">
        <div className="h-4 w-32 bg-white/10 rounded" />
        <div className="h-16 bg-white/5 rounded-xl" />
        <div className="h-16 bg-white/5 rounded-xl" />
      </div>
    );
  }

  if (status === "not_in_plan") {
    return (
      <p className="font-body-md text-body-md text-on-surface-variant">
        Centinela Fiscal no está en tu plan actual.
      </p>
    );
  }

  if (alerts.length === 0) return null;

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-medium uppercase tracking-wider text-on-surface-variant">
            Alertas Activas
          </h2>
          <span className="px-1.5 py-0.5 rounded-full bg-warning/20 border border-warning/30 text-warning text-[10px] font-semibold tabular-nums leading-none">
            {alerts.length}
          </span>
        </div>
      </div>
      <div className="flex flex-col gap-2.5">
        {alerts.map((alert) => {
          const accent = SEVERITY_ACCENT[alert.severity];
          return (
            <div
              key={alert.id}
              className={`p-3 rounded-xl bg-surface-container/60 backdrop-blur-md border border-outline-variant/40 border-l-[3px] ${accent.border} flex items-start gap-3`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${accent.iconBg} ${accent.iconColor}`}
              >
                <span className="material-symbols-outlined text-[17px]">{alert.icon}</span>
              </div>
              <p className="flex-1 text-[13px] text-on-surface leading-snug">{alert.message}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
