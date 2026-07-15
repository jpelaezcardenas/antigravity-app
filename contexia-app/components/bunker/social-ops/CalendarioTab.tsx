"use client";

import { useEffect, useState } from "react";
import { getSocialOpsCalendario, type Calendario } from "@/lib/social-ops-api";

const PILAR_STYLES: Record<string, string> = {
  CLARIDAD: "bg-primary/15 text-primary-container border-primary/30",
  PROTECCION: "bg-status-warning/15 text-status-warning border-status-warning/30",
  ACCION: "bg-status-success/15 text-status-success border-status-success/30",
  COMUNIDAD: "bg-secondary/15 text-secondary-fixed border-secondary/30",
};

const STATUS_STYLES: Record<string, string> = {
  PLANIFICADO: "bg-white/5 text-on-surface-variant",
  EN_PRODUCCION: "bg-status-warning/15 text-status-warning",
  DRAFT: "bg-white/5 text-on-surface-variant",
  REVIEW: "bg-secondary/15 text-secondary-fixed",
  APPROVED: "bg-status-success/15 text-status-success",
  PUBLISHED: "bg-primary/15 text-primary-container",
};

const STATUS_LABELS: Record<string, string> = {
  PLANIFICADO: "Planificado",
  EN_PRODUCCION: "En Producción",
  DRAFT: "Borrador",
  REVIEW: "En Revisión",
  APPROVED: "Aprobado",
  PUBLISHED: "Publicado",
};

export function CalendarioTab() {
  const [entries, setEntries] = useState<Calendario[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedSemana, setSelectedSemana] = useState<number>(1);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getSocialOpsCalendario(selectedSemana)
      .then((res) => {
        if (!cancelled) setEntries(res.items || []);
      })
      .catch(() => {
        if (!cancelled) setEntries([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSemana]);

  const getDayLabel = (dateStr: string): string => {
    const date = new Date(dateStr + "T12:00:00");
    return date.toLocaleDateString("es-CO", { weekday: "short", day: "numeric", month: "short" });
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-surface-container rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-sm text-on-surface-variant">Semana:</span>
        <div className="flex gap-1">
          {[1, 2, 3, 4].map((week) => (
            <button
              key={week}
              onClick={() => setSelectedSemana(week)}
              className={`px-4 py-1.5 text-sm rounded-lg transition-all ${
                selectedSemana === week
                  ? "bg-primary/20 text-primary-container border border-primary/30"
                  : "bg-surface-container text-on-surface-variant border border-outline-variant/20 hover:bg-white/5"
              }`}
            >
              S{week}
            </button>
          ))}
        </div>
        <span className="text-xs text-on-surface-variant ml-auto font-mono">{entries.length} posts planificados</span>
      </div>

      {entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <div className="w-20 h-20 rounded-2xl bg-secondary/10 border border-secondary/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-4xl text-secondary-fixed">calendar_month</span>
          </div>
          <h3 className="text-lg font-semibold text-on-surface-variant">Calendario vacío</h3>
          <p className="text-sm text-on-surface-variant max-w-md text-center">
            No hay publicaciones planificadas para la semana {selectedSemana}. Selecciona ideas desde el Kanban y
            agrégalas al calendario editorial.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <div
              key={entry.id}
              onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
              className="group bg-surface-elevated border border-outline-variant/20 rounded-xl overflow-hidden cursor-pointer hover:border-primary/30 transition-all"
            >
              <div className="flex items-center gap-4 p-4">
                <div className="flex-shrink-0 w-20 text-center">
                  <p className="text-xs font-semibold text-primary-container uppercase tracking-wide">
                    {getDayLabel(entry.fecha_publicacion)}
                  </p>
                </div>
                <div className="w-px h-10 bg-outline-variant/30" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-on-surface truncate">{entry.titulo_trabajo || "Sin título"}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {entry.pilar && (
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${PILAR_STYLES[entry.pilar] ?? ""}`}>
                        {entry.pilar}
                      </span>
                    )}
                    {entry.formato && <span className="text-[10px] text-on-surface-variant">{entry.formato}</span>}
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <span className={`text-[11px] font-medium px-3 py-1 rounded-full ${STATUS_STYLES[entry.status] ?? ""}`}>
                    {STATUS_LABELS[entry.status] ?? entry.status}
                  </span>
                </div>
                <span className={`text-on-surface-variant/60 text-xs transition-transform ${expandedId === entry.id ? "rotate-180" : ""}`}>
                  ▼
                </span>
              </div>

              {expandedId === entry.id && (
                <div className="border-t border-outline-variant/20 bg-white/5 p-4 space-y-2">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-on-surface-variant text-xs">Responsable</span>
                      <p className="text-on-surface-variant">{entry.responsable}</p>
                    </div>
                    <div>
                      <span className="text-on-surface-variant text-xs">Formato</span>
                      <p className="text-on-surface-variant">{entry.formato || "—"}</p>
                    </div>
                  </div>
                  {entry.notas_editoriales && (
                    <div>
                      <span className="text-on-surface-variant text-xs">Notas Editoriales</span>
                      <p className="text-on-surface-variant text-sm mt-0.5">{entry.notas_editoriales}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
