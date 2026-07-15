"use client";

import { useEffect, useMemo, useState } from "react";
import { getSocialOpsMetrics, simulateSocialOpsMetrics, type Metrica, type Publicacion } from "@/lib/social-ops-api";

const CLASIFICACION_STYLES: Record<string, string> = {
  GANADOR: "bg-status-success/20 text-status-success border border-status-success/40",
  PROMEDIO: "bg-status-warning/20 text-status-warning border border-status-warning/40",
  PERDEDOR: "bg-status-critical/20 text-status-critical border border-status-critical/40",
};

const clasificacionLabels: Record<string, string> = {
  GANADOR: "Ganador",
  PROMEDIO: "Promedio",
  PERDEDOR: "Perdedor",
};

export function MetricasTab() {
  const [metricas, setMetricas] = useState<Metrica[]>([]);
  const [publicaciones, setPublicaciones] = useState<Publicacion[]>([]);
  const [source, setSource] = useState<"supabase" | "demo_fallback">("demo_fallback");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getSocialOpsMetrics();
      setSource(res.source);
      setMetricas(res.metricas || []);
      setPublicaciones(res.publicaciones || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar métricas");
      setMetricas([]);
      setPublicaciones([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const computed = useMemo(() => {
    const totalAlcance = metricas.reduce((sum, m) => sum + (Number(m.alcance) || 0), 0);
    const avgEngagement =
      metricas.length > 0
        ? (metricas.reduce((sum, m) => sum + Number(m.engagement_rate || 0), 0) / metricas.length).toFixed(2)
        : "0.00";
    const bestScore = metricas.length > 0 ? Math.max(...metricas.map((m) => m.score ?? 0)) : 0;
    const totalPosts = publicaciones.length > 0 ? publicaciones.length : new Set(metricas.map((m) => m.pub_id)).size;
    return { totalAlcance, avgEngagement, bestScore, totalPosts };
  }, [metricas, publicaciones]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-surface-container rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-surface-container rounded-xl animate-pulse" />
      </div>
    );
  }

  const empty = metricas.length === 0 && publicaciones.length === 0;

  if (empty) {
    return (
      <div className="space-y-6">
        {error && (
          <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-4 text-status-critical text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Alcance Total", value: "—", icon: "visibility" },
            { label: "Engagement", value: "—", icon: "chat_bubble" },
            { label: "Posts", value: "0", icon: "description" },
            { label: "Mejor Score", value: "—", icon: "emoji_events" },
          ].map((card) => (
            <div key={card.label} className="bg-surface-container border border-outline-variant/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="material-symbols-outlined text-lg text-on-surface-variant">{card.icon}</span>
                <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">{card.label}</span>
              </div>
              <p className="text-2xl font-bold text-on-surface-variant">{card.value}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-center justify-center py-16 space-y-4 bg-surface-container rounded-xl border border-outline-variant/20">
          <div className="w-24 h-24 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-5xl text-primary-container">bar_chart</span>
          </div>
          <h3 className="text-lg font-semibold text-on-surface-variant">Aún no hay métricas</h3>
          <p className="text-sm text-on-surface-variant max-w-lg text-center leading-relaxed">
            Las métricas aparecerán aquí cuando se publique contenido y se sincronice desde integraciones
            (Meta/TikTok/LinkedIn) o se registre desde el core. Cada publicación se clasifica como Ganador,
            Promedio o Perdedor según su score.
          </p>
          <button
            onClick={async () => {
              try {
                setLoading(true);
                await simulateSocialOpsMetrics();
                await load();
              } catch (e) {
                setError(e instanceof Error ? e.message : "No se pudo simular métricas");
                setLoading(false);
              }
            }}
            className="mt-2 px-5 py-2 rounded-xl bg-primary-fixed-dim hover:bg-primary text-on-primary text-sm font-semibold"
          >
            Simular métricas
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-4 text-status-critical text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-surface-container border border-outline-variant/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-lg text-on-surface-variant">visibility</span>
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Alcance Total</span>
          </div>
          <p className="text-2xl font-bold text-primary-container">{computed.totalAlcance.toLocaleString("es-CO")}</p>
        </div>
        <div className="bg-surface-container border border-outline-variant/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-lg text-on-surface-variant">chat_bubble</span>
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Engagement</span>
          </div>
          <p className="text-2xl font-bold text-secondary-fixed">{computed.avgEngagement}%</p>
        </div>
        <div className="bg-surface-container border border-outline-variant/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-lg text-on-surface-variant">description</span>
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Posts</span>
          </div>
          <p className="text-2xl font-bold text-status-success">{computed.totalPosts}</p>
        </div>
        <div className="bg-surface-container border border-outline-variant/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-lg text-on-surface-variant">emoji_events</span>
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Mejor Score</span>
          </div>
          <p className="text-2xl font-bold text-status-warning">{computed.bestScore || "—"}</p>
        </div>
      </div>

      <div className="bg-surface-elevated border border-outline-variant/20 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-outline-variant/20 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-on-surface-variant">Detalle por Publicación</h3>
          <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">source: {source}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[11px] text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">
                <th className="px-4 py-3 text-left">Fecha</th>
                <th className="px-4 py-3 text-right">Alcance</th>
                <th className="px-4 py-3 text-right">Reacciones</th>
                <th className="px-4 py-3 text-right">Comentarios</th>
                <th className="px-4 py-3 text-right">Compartidos</th>
                <th className="px-4 py-3 text-right">Engagement</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3 text-center">Clase</th>
              </tr>
            </thead>
            <tbody>
              {metricas.map((m) => (
                <tr key={m.id} className="border-b border-outline-variant/10 hover:bg-white/5 transition">
                  <td className="px-4 py-3 text-on-surface-variant font-mono text-xs">{m.fecha_captura}</td>
                  <td className="px-4 py-3 text-right text-on-surface-variant">{Number(m.alcance).toLocaleString("es-CO")}</td>
                  <td className="px-4 py-3 text-right text-on-surface-variant">{m.reacciones}</td>
                  <td className="px-4 py-3 text-right text-on-surface-variant">{m.comentarios}</td>
                  <td className="px-4 py-3 text-right text-on-surface-variant">{m.compartidos}</td>
                  <td className="px-4 py-3 text-right text-primary-container font-semibold">
                    {Number(m.engagement_rate).toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right text-status-warning font-bold">{m.score ?? "—"}</td>
                  <td className="px-4 py-3 text-center">
                    {m.clasificacion ? (
                      <span
                        className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${
                          CLASIFICACION_STYLES[m.clasificacion] || "bg-white/5 text-on-surface-variant border border-outline-variant/30"
                        }`}
                      >
                        {clasificacionLabels[m.clasificacion] ?? m.clasificacion}
                      </span>
                    ) : (
                      <span className="text-on-surface-variant/50">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
