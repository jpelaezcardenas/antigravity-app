"use client";

import { useEffect, useState } from "react";
import { formatShortDate } from "@/lib/format";
import { fetchFinancials, type TaxMilestone } from "@/lib/api-client";

/**
 * "Próximos Hitos" — real DIAN calendar deadlines for the tenant's real NIT
 * (backend: core/dian_tax_calendar.py::next_tax_milestones, wired into
 * `GET /financials.next_milestones`). Self-feeding like ActiveAlertsV2: its
 * own `fetchFinancials()` call, no props.
 *
 * DELIBERATE scope reduction from the Stitch mockup: the mockup shows a peso
 * amount per hito ("$3.4M Ret. DIAN"); this renders date only. No table in
 * this repo tracks a real per-tenant amount due for either obligation (no
 * CxC/CxP-with-due-date model — same honesty gap already declared by the
 * Radar de Caja endpoint, ARCHITECTURE.md's Flujo estrella section) — an
 * amount here would be fabricated. Renders nothing when the tenant has no
 * NIT on file (empty `next_milestones`).
 */
export function NextMilestonesV2() {
  const [milestones, setMilestones] = useState<TaxMilestone[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchFinancials()
      .then((snapshot) => {
        if (cancelled) return;
        setMilestones(snapshot.next_milestones ?? []);
      })
      .catch((error) => {
        console.warn("[NextMilestonesV2] financials fetch failed", error);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (milestones.length === 0) return null;

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs font-medium uppercase tracking-wider text-on-surface-variant">
          Próximos hitos
        </h2>
        <span className="text-xs text-on-surface-variant/60">DIAN</span>
      </div>
      <div className="flex gap-2.5">
        {milestones.map((milestone) => (
          <div
            key={milestone.id}
            className="flex-1 px-3 py-3 rounded-xl bg-surface-container/60 backdrop-blur-md border border-outline-variant/40"
          >
            <p className="text-[11px] text-on-surface-variant leading-tight">
              {milestone.label}
            </p>
            <p className="text-lg font-semibold text-on-surface tabular-nums mt-1">
              {formatShortDate(milestone.date)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
