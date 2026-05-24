"use client";

import { useState, useEffect } from "react";
import { evaluateCentinela } from "@/lib/services/api";
import type { CentinelaEvaluateResponse, SeverityLevel, RiskLevel } from "@/lib/types/centinela";

interface CentinelaAlertsCardProps {
  company_id: string;
  financialData?: Record<string, unknown>;
  autoRefresh?: boolean; // Auto-refresh every 5 minutes
}

export function CentinelaAlertsCard({
  company_id,
  financialData = {},
  autoRefresh = false,
}: CentinelaAlertsCardProps) {
  const [data, setData] = useState<CentinelaEvaluateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await evaluateCentinela({
        company_id,
        financial_data: financialData,
        save_alerts: false, // Don't persist during dashboard preview
      });
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount
  useEffect(() => {
    fetchAlerts();
  }, [company_id]);

  // Auto-refresh if enabled
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchAlerts, 5 * 60 * 1000); // 5 minutes
    return () => clearInterval(interval);
  }, [company_id, autoRefresh]);

  const getSeverityColor = (severity: SeverityLevel) => {
    return severity === "critical"
      ? "bg-error/10 border-error/30 text-error"
      : "bg-warning/10 border-warning/30 text-warning";
  };

  const getSeverityIcon = (severity: SeverityLevel) => {
    return severity === "critical" ? "error" : "warning";
  };

  const getRiskLevelColor = (risk: RiskLevel) => {
    switch (risk) {
      case "critical":
        return "bg-error text-on-error";
      case "high":
        return "bg-error/50 text-on-error";
      case "medium":
        return "bg-warning text-on-warning";
      case "low":
        return "bg-success text-on-success";
    }
  };

  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 overflow-hidden shadow-[0_4px_24px_rgba(45,212,191,0.05)]">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined icon-fill text-primary-container mt-1">
            shield_alert
          </span>
          <div>
            <h3 className="font-title-md text-title-md text-on-surface">
              Centinela — Detección Fiscal
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
              Análisis ex-ante de 10 reglas fiscales colombianas
            </p>
          </div>
        </div>

        {/* Risk Level Badge */}
        {data && (
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-label-sm font-semibold whitespace-nowrap ${getRiskLevelColor(data.risk_level)}`}
          >
            {data.risk_level === "critical"
              ? "⚠️ Crítico"
              : data.risk_level === "high"
                ? "🔴 Alto"
                : data.risk_level === "medium"
                  ? "🟡 Medio"
                  : "🟢 Bajo"}
          </span>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8 gap-3">
          <div className="relative w-4 h-4">
            <div className="absolute inset-0 rounded-full border-2 border-primary/20"></div>
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin"></div>
          </div>
          <p className="text-label-sm text-on-surface-variant">Analizando reglas...</p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="p-4 rounded-lg bg-error/10 border border-error/30 flex items-start gap-3">
          <span className="material-symbols-outlined text-error mt-0.5">error</span>
          <div>
            <h4 className="font-semibold text-error text-label-sm">Error al evaluar</h4>
            <p className="text-error/80 text-label-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Data State */}
      {data && !loading && (
        <div className="flex flex-col gap-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-surface border border-outline">
              <div className="text-label-sm text-on-surface-variant">Alertas</div>
              <div className="text-headline-md text-on-surface font-bold">
                {data.alert_count}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-surface border border-outline">
              <div className="text-label-sm text-on-surface-variant">Críticas</div>
              <div className="text-headline-md text-error font-bold">{data.critical_count}</div>
            </div>
            <div className="p-3 rounded-lg bg-surface border border-outline">
              <div className="text-label-sm text-on-surface-variant">Advertencias</div>
              <div className="text-headline-md text-warning font-bold">{data.warning_count}</div>
            </div>
          </div>

          {/* Alerts List */}
          {data.alerts.length > 0 ? (
            <div className="flex flex-col gap-3">
              <div className="text-label-sm font-semibold text-on-surface">
                Reglas Activadas
              </div>
              {data.alerts.map((alert) => (
                <div
                  key={alert.rule_id}
                  className={`p-4 rounded-lg border flex gap-3 ${getSeverityColor(alert.severity)}`}
                >
                  <span className="material-symbols-outlined mt-0.5 flex-shrink-0">
                    {getSeverityIcon(alert.severity)}
                  </span>
                  <div className="flex-1">
                    <h4 className="font-semibold text-label-md">{alert.rule_name}</h4>
                    <p className="text-label-sm opacity-90 mt-1">{alert.title}</p>
                    <p className="text-label-sm opacity-75 mt-2 italic">
                      {alert.recommendation}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-lg bg-success/10 border border-success/30 flex items-start gap-3">
              <span className="material-symbols-outlined text-success mt-0.5">
                check_circle
              </span>
              <div>
                <h4 className="font-semibold text-success text-label-sm">
                  Sin alertas detectadas
                </h4>
                <p className="text-success/80 text-label-sm mt-1">
                  La empresa cumple con todas las reglas fiscales evaluadas
                </p>
              </div>
            </div>
          )}

          {/* Last Updated */}
          {lastUpdated && (
            <div className="text-label-xs text-on-surface-variant/60 pt-2">
              Actualizado: {lastUpdated.toLocaleTimeString("es-CO")}
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={fetchAlerts}
            disabled={loading}
            className="px-4 py-2 rounded-lg border border-outline text-label-sm font-semibold text-on-surface hover:bg-surface-variant disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Actualizar análisis
          </button>
        </div>
      )}
    </section>
  );
}
