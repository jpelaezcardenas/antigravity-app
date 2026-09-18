"use client";

import { useEffect, useState } from "react";
import { fetchCentinelaAlerts, type CentinelaAlert } from "@/lib/api-client";
import { MetricTileGrid, type MetricTile } from "@/components/shared/v2/MetricTileGrid";

/**
 * PWA V2 (reconstructed 2026-09-18) — the first cut of this component rendered
 * every real alert as its own long text card (title + full CUFE description),
 * unbounded — 20 real alerts turned Pulso into a scrolling alert feed instead
 * of the Stitch-approved "ALERTAS ACTIVAS · Por prioridad" 2-tile summary
 * (founder screenshot from the approved Stitch mockup: "Retención DIAN: 3
 * días" / "Conciliación: Al día").
 *
 * That mockup's tiles imply a due-date countdown ("3 días") that has no
 * backing field anywhere — CentinelaAlert has no due-date, only
 * rule_id/severity/title/description. Rather than invent one, the tiles here
 * use the response's own real aggregate fields (critical_count/warning_count)
 * — grouping by severity, not a fabricated deadline (founder decision,
 * 2026-09-18). Tapping a tile expands that severity's real alerts below,
 * full title+description intact — nothing hidden, just not all dumped inline
 * by default.
 *
 * Same fetchCentinelaAlerts contract and honesty rules as ActiveAlerts.tsx
 * (never falls back to mock on error/empty).
 */
export function ActiveAlertsV2() {
  const [alerts, setAlerts] = useState<CentinelaAlert[]>([]);
  const [criticalCount, setCriticalCount] = useState(0);
  const [warningCount, setWarningCount] = useState(0);
  const [status, setStatus] = useState<"loading" | "ready" | "not_in_plan">("loading");
  const [expanded, setExpanded] = useState<"critical" | "warning" | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchCentinelaAlerts()
      .then((response) => {
        if (cancelled) return;
        if (response.status === "not_in_plan") {
          setStatus("not_in_plan");
          return;
        }
        setAlerts(response.alerts);
        setCriticalCount(response.critical_count);
        setWarningCount(response.warning_count);
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        console.warn("[ActiveAlertsV2] centinela alerts fetch failed", error);
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
        <div className="grid grid-cols-2 gap-3">
          <div className="h-20 bg-white/5 rounded-2xl" />
          <div className="h-20 bg-white/5 rounded-2xl" />
        </div>
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

  if (criticalCount === 0 && warningCount === 0) return null;

  const tiles: MetricTile[] = [
    {
      id: "critical",
      icon: "rule_folder",
      label: "Críticas",
      value: String(criticalCount),
      accent: "critical",
      onClick: criticalCount > 0 ? () => setExpanded(expanded === "critical" ? null : "critical") : undefined,
      selected: expanded === "critical",
    },
    {
      id: "warning",
      icon: "schedule",
      label: "Advertencias",
      value: String(warningCount),
      accent: "warning",
      onClick: warningCount > 0 ? () => setExpanded(expanded === "warning" ? null : "warning") : undefined,
      selected: expanded === "warning",
    },
  ];

  const totalCount = criticalCount + warningCount;

  const expandedAlerts = expanded
    ? alerts.filter((a) => (expanded === "critical" ? a.severity === "critical" : a.severity !== "critical"))
    : [];

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-medium uppercase tracking-wider text-on-surface-variant">
            Alertas activas
          </h2>
          <span className="px-1.5 py-0.5 rounded-full bg-warning/20 border border-warning/30 text-warning text-[10px] font-semibold tabular-nums leading-none">
            {totalCount}
          </span>
        </div>
        <span className="text-xs text-on-surface-variant/60">Por prioridad</span>
      </div>

      <MetricTileGrid tiles={tiles} variant="priority" />

      {expanded && (
        <div className="flex flex-col gap-2.5 mt-1">
          {expandedAlerts.map((alert, index) => (
            <div
              key={`${alert.rule_id}-${index}`}
              className={`p-3 rounded-xl bg-surface-container/60 backdrop-blur-md border border-outline-variant/40 border-l-[3px] ${
                alert.severity === "critical" ? "border-l-status-critical" : "border-l-warning"
              }`}
            >
              <p className="text-[13px] font-semibold text-on-surface">{alert.title}</p>
              <p className="text-[12px] text-on-surface-variant leading-snug mt-0.5">
                {alert.description}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
