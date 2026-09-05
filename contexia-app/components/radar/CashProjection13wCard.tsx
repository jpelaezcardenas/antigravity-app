"use client";

import { useEffect, useState } from "react";
import { formatCop } from "@/lib/format";
import { CARD_SHADOW } from "@/lib/styles/cardStyles";
import {
  fetchCashProjection13w,
  type CashProjection13wSnapshot,
  type CashProjectionWeek,
} from "@/lib/api-client";

/**
 * Radar de Caja — 13-week cash projection (radar-cash-projection-13w).
 *
 * Self-feeding, read-only, like CashTodayCard: no data props, explicit
 * loading / ready / sin_historico_suficiente / tenant_no_resuelto / error
 * states, and never falls back to radarMock (contexia-app/CLAUDE.md hard rule).
 *
 * The chart is plain inline SVG — same technique as CashProjectionCard, no
 * charting library (design.md Decision #6).
 */

// Two confidence bands only. "alta" does not exist under the solo_historico
// methodology, so there is deliberately no third color here.
const CONFIDENCE_STROKE: Record<CashProjectionWeek["confianza"], string> = {
  media: "#2DD4BF",
  baja: "#94A3B8",
};

const CHART_VIEWBOX_SIZE = 100;

/**
 * Normalize weekly balances into a "M x,y L x,y ..." path inside a
 * 0 0 100 100 viewBox. Y is inverted (SVG y grows downward) so a rising
 * balance rises visually. A flat series renders as a centered flat line.
 */
function buildProjectionPath(semanas: CashProjectionWeek[]): string {
  const values = semanas.map((week) => week.caja_proyectada);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;

  return semanas
    .map((week, index) => {
      const x = (index / (semanas.length - 1)) * CHART_VIEWBOX_SIZE;
      const normalized = span === 0 ? 0.5 : (week.caja_proyectada - min) / span;
      // Inset 10% top and bottom so the line never touches the card edges.
      const y = CHART_VIEWBOX_SIZE - (normalized * 0.8 + 0.1) * CHART_VIEWBOX_SIZE;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

/** Index at which confidence drops from "media" to "baja", as a 0-100 percentage. */
function confidenceSplitPct(semanas: CashProjectionWeek[]): number | null {
  const firstBaja = semanas.findIndex((week) => week.confianza === "baja");
  if (firstBaja <= 0) return null;
  return (firstBaja / (semanas.length - 1)) * 100;
}

function CardShell({ children }: { children: React.ReactNode }) {
  return (
    <section
      className={`bg-surface-elevated rounded-xl border border-white/10 p-5 flex flex-col gap-4 ${CARD_SHADOW.base}`}
    >
      <div>
        <h3 className="font-title-md text-title-md text-primary-container">
          Radar de Caja — 13 semanas
        </h3>
        <p className="font-data-mono text-data-mono text-on-surface-variant mt-1">
          Hacia dónde va tu plata
        </p>
      </div>
      {children}
    </section>
  );
}

export function CashProjection13wCard() {
  const [snapshot, setSnapshot] = useState<CashProjection13wSnapshot | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "empty" | "error">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchCashProjection13w()
      .then((data) => {
        if (cancelled) return;
        if (data.estado !== "ok" || !data.semanas || data.semanas.length === 0) {
          setSnapshot(data);
          setStatus("empty");
          return;
        }
        setSnapshot(data);
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        // Never fall back to radarMock — an honest, quiet error state instead.
        console.warn("[CashProjection13wCard] cash projection fetch failed", error);
        setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <CardShell>
        <div className="animate-pulse flex flex-col gap-3">
          <div className="h-[180px] w-full bg-white/5 rounded" />
          <div className="h-5 w-3/4 bg-white/10 rounded" />
        </div>
      </CardShell>
    );
  }

  if (status === "error") {
    return (
      <CardShell>
        <p className="font-body-md text-body-md text-on-surface-variant">
          No pudimos calcular tu proyección de caja en este momento. Intenta de nuevo más tarde.
        </p>
      </CardShell>
    );
  }

  if (status === "empty" || !snapshot?.semanas) {
    const message =
      snapshot?.estado === "sin_historico_suficiente"
        ? "Aún no tenemos suficiente historial para proyectar tu caja con confianza. Cuando tengas unas semanas más de movimientos, aquí verás hacia dónde va tu plata."
        : "Todavía no podemos mostrarte esta proyección.";

    return (
      <CardShell>
        <p className="font-body-md text-body-md text-on-surface-variant">{message}</p>
      </CardShell>
    );
  }

  const semanas = snapshot.semanas;
  const pathD = buildProjectionPath(semanas);
  const splitPct = confidenceSplitPct(semanas);
  const firstWeek = semanas[0];
  const lastWeek = semanas[semanas.length - 1];

  return (
    <CardShell>
      <div className="h-[180px] w-full relative mt-2 border-b border-l border-outline-variant/30">
        {/* Grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="w-full h-px bg-outline-variant/10" />
          ))}
        </div>

        {/* Area gradient under the curve */}
        <div className="absolute bottom-0 left-0 right-0 h-[70%] bg-gradient-to-t from-primary/20 to-transparent blur-[2px]" />

        <svg
          className="absolute inset-0 w-full h-full"
          preserveAspectRatio="none"
          viewBox={`0 0 ${CHART_VIEWBOX_SIZE} ${CHART_VIEWBOX_SIZE}`}
          aria-hidden
        >
          <defs>
            {/* Two-band confidence coding: teal while "media", gray once "baja". */}
            <linearGradient id="confidenceStroke" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor={CONFIDENCE_STROKE.media} />
              {splitPct !== null && (
                <>
                  <stop offset={`${splitPct}%`} stopColor={CONFIDENCE_STROKE.media} />
                  <stop offset={`${splitPct}%`} stopColor={CONFIDENCE_STROKE.baja} />
                </>
              )}
              <stop offset="100%" stopColor={splitPct === null ? CONFIDENCE_STROKE.media : CONFIDENCE_STROKE.baja} />
            </linearGradient>
          </defs>
          <path
            d={pathD}
            fill="none"
            stroke="url(#confidenceStroke)"
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>

      {/* X-axis: first and last week only — 13 labels never fit on mobile. */}
      <div className="flex justify-between font-label-caps text-label-caps text-on-surface-variant/60">
        <span>Sem 1</span>
        <span>Sem {lastWeek.semana}</span>
      </div>

      {/* Confidence legend — two bands, never a third. */}
      <div className="flex flex-wrap gap-4">
        <span className="flex items-center gap-2 font-label-caps text-label-caps text-on-surface-variant">
          <span
            className="w-3 h-0.5 rounded-full"
            style={{ backgroundColor: CONFIDENCE_STROKE.media }}
          />
          Confianza media (sem 1-4)
        </span>
        <span className="flex items-center gap-2 font-label-caps text-label-caps text-on-surface-variant">
          <span
            className="w-3 h-0.5 rounded-full"
            style={{ backgroundColor: CONFIDENCE_STROKE.baja }}
          />
          Confianza baja (sem 5-13)
        </span>
      </div>

      <div className="flex justify-between items-center border-t border-outline-variant/30 pt-4">
        <div className="flex flex-col">
          <span className="font-label-caps text-label-caps text-on-surface-variant">Hoy</span>
          <span className="font-data-mono text-data-mono text-on-surface">
            {formatCop(Math.round(firstWeek.caja_proyectada / 100))}
          </span>
        </div>
        <div className="flex flex-col items-end">
          <span className="font-label-caps text-label-caps text-on-surface-variant">
            En 13 semanas
          </span>
          <span className="font-data-mono text-data-mono text-on-surface">
            {formatCop(Math.round(lastWeek.caja_proyectada / 100))}
          </span>
        </div>
      </div>

      {snapshot.alerta_narrativa && (
        <p className="font-body-md text-body-md text-on-surface leading-relaxed">
          {snapshot.alerta_narrativa}
        </p>
      )}

      {/* Honest methodology footnote — never imply precision we don't have. */}
      <p className="font-label-caps text-label-caps text-on-surface-variant/60">
        Proyección basada en tu historial de movimientos. No incluye facturas por cobrar o pagar
        con fecha, ni impuestos futuros estimados.
      </p>
    </CardShell>
  );
}
