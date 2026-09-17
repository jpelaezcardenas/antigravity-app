"use client";

import { useEffect, useState } from "react";
import {
  fetchCashProjection13w,
  type CashProjection13wSnapshot,
  type CashProjectionWeek,
} from "@/lib/api-client";
import { MetricTileGrid, type MetricTile } from "@/components/shared/v2/MetricTileGrid";

/**
 * PWA V2 — Stitch-approved metric-tile summary for the 13-week cash
 * projection (radar-cash-projection-13w), self-feeding like
 * CashProjection13wCard. Every tile is derived straight from the real
 * fetch — confidence bands, methodology and the future-tax field are the
 * same honestly-declared values that component already renders, just in
 * tile form instead of a legend. Never falls back to radarMock.
 */

const CONFIDENCE_LABEL: Record<CashProjectionWeek["confianza"], string> = {
  media: "Confianza media",
  baja: "Confianza baja",
};

function tilesFromSnapshot(snapshot: CashProjection13wSnapshot): MetricTile[] {
  const semanas = snapshot.semanas ?? [];
  const firstBand = semanas.find((w) => w.semana <= 4)?.confianza ?? "media";
  const secondBand = semanas.find((w) => w.semana >= 5)?.confianza ?? "baja";

  return [
    {
      id: "week-1-4",
      icon: "calendar_view_week",
      label: "Semana 1-4",
      value: CONFIDENCE_LABEL[firstBand],
      accent: firstBand === "media" ? "success" : "warning",
    },
    {
      id: "week-5-13",
      icon: "calendar_month",
      label: "Semana 5-13",
      value: CONFIDENCE_LABEL[secondBand],
      accent: secondBand === "media" ? "success" : "warning",
    },
    {
      id: "methodology",
      icon: "history",
      label: "Metodología",
      value: snapshot.metodologia === "solo_historico" ? "Histórica" : snapshot.metodologia,
    },
    {
      id: "future-tax",
      icon: "help",
      label: "Impuesto futuro",
      value:
        snapshot.impuesto_futuro_estimado === null
          ? "No calculado"
          : String(snapshot.impuesto_futuro_estimado),
    },
  ];
}

export function RadarCashProjectionTiles() {
  const [snapshot, setSnapshot] = useState<CashProjection13wSnapshot | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "empty" | "error">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchCashProjection13w()
      .then((data) => {
        if (cancelled) return;
        if (data.estado !== "ok" || !data.semanas || data.semanas.length === 0) {
          setStatus("empty");
          return;
        }
        setSnapshot(data);
        setStatus("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        console.warn("[RadarCashProjectionTiles] cash projection fetch failed", error);
        setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <div className="grid grid-cols-2 gap-3">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-20 rounded-2xl bg-white/5 animate-pulse" />
        ))}
      </div>
    );
  }

  if (status !== "ready" || !snapshot) {
    return null;
  }

  return <MetricTileGrid tiles={tilesFromSnapshot(snapshot)} />;
}
