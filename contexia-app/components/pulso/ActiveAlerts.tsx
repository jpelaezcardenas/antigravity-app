"use client";

import { useEffect, useState } from "react";
import type { ActiveAlert, AlertSeverity } from "@/lib/types/contexia";
import { SEVERITY_ICON_STYLES } from "@/lib/styles/statusStyles";
import { fetchCentinelaAlerts, type CentinelaAlert } from "@/lib/api-client";

const SEVERITY_ICON: Record<AlertSeverity, string> = {
  warning: "schedule",
  critical: "rule_folder",
};

function toSeverity(backendSeverity: string): AlertSeverity {
  return backendSeverity === "critical" ? "critical" : "warning";
}

function toActiveAlert(alert: CentinelaAlert, index: number): ActiveAlert {
  const severity = toSeverity(alert.severity);
  return {
    // rule_id is NOT unique per alert row (the same rule can fire once per
    // affected document — confirmed live, e.g. many SHADOW_GL_DISCREPANCY
    // rows share one rule_id), so the index must always be part of the key
    // or React logs duplicate-key warnings and can misrender the list.
    id: `${alert.rule_id || "alert"}-${index}`,
    icon: SEVERITY_ICON[severity],
    severity,
    message: alert.description ? `${alert.title} — ${alert.description}` : alert.title,
  };
}

function AlertsSkeleton() {
  return (
    <section className="flex flex-col gap-3 animate-pulse">
      <div className="h-6 w-40 bg-white/10 rounded mb-1" />
      <div className="bg-surface-elevated rounded-xl p-4 border border-white/10 h-16" />
      <div className="bg-surface-elevated rounded-xl p-4 border border-white/10 h-16" />
    </section>
  );
}

export function ActiveAlerts() {
  const [alerts, setAlerts] = useState<ActiveAlert[]>([]);
  const [status, setStatus] = useState<"loading" | "ready">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchCentinelaAlerts()
      .then((response) => {
        if (cancelled) return;
        setAlerts(response.alerts.map(toActiveAlert));
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        // Honest empty-on-error — no fallback to pulsoMock.alerts (spec
        // "No alerts or a fetch error renders nothing, not a mock or a crash").
        console.warn("[ActiveAlerts] centinela alerts fetch failed", error);
        setAlerts([]);
        setStatus("ready");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return <AlertsSkeleton />;
  }

  if (alerts.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <h3 className="font-title-md text-title-md text-primary-container mb-1">
        Alertas Activas
      </h3>
      {alerts.map((alert) => {
        const styles = SEVERITY_ICON_STYLES[alert.severity];
        return (
          <div
            key={alert.id}
            className={`bg-surface-elevated rounded-xl p-4 border flex items-start gap-4 ${styles.border}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${styles.iconBg}`}
            >
              <span
                className={`material-symbols-outlined text-sm ${styles.iconColor}`}
              >
                {alert.icon}
              </span>
            </div>
            <div className="flex-1">
              <p className="font-body-md text-body-md text-on-surface">
                {alert.message}
              </p>
            </div>
            <button
              type="button"
              aria-label="Ver detalle"
              className="w-8 h-8 flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors"
            >
              <span className="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
        );
      })}
    </section>
  );
}
