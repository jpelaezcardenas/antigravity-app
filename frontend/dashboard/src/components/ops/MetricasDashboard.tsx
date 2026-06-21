import React, { useEffect, useMemo, useState } from 'react';

type Metrica = {
  id: number;
  pub_id: number;
  fecha_captura: string;
  alcance: number;
  impresiones: number;
  reacciones: number;
  comentarios: number;
  compartidos: number;
  engagement_rate: number;
  score?: number | null;
  clasificacion?: 'GANADOR' | 'PROMEDIO' | 'PERDEDOR' | null;
};

type Publicacion = {
  id: number;
  fecha_publicacion_real: string | null;
  plataforma: string;
};

const CLASIFICACION_STYLES: Record<string, string> = {
  GANADOR:
    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-emerald-500/10 shadow-lg',
  PROMEDIO: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40',
  PERDEDOR: 'bg-red-500/20 text-red-300 border border-red-500/40',
};

const clasificacionLabels: Record<string, string> = {
  GANADOR: 'Ganador',
  PROMEDIO: 'Promedio',
  PERDEDOR: 'Perdedor',
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
  const resp = await fetch(`${base}${path}`, {
    ...init,
    headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...(init?.headers || {}) },
  });
  if (!resp.ok) throw new Error(await resp.text());
  return (await resp.json()) as T;
}

export default function MetricasDashboard() {
  const [metricas, setMetricas] = useState<Metrica[]>([]);
  const [publicaciones, setPublicaciones] = useState<Publicacion[]>([]);
  const [source, setSource] = useState<'supabase' | 'demo_fallback'>('demo_fallback');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api<{
        source: 'supabase' | 'demo_fallback';
        summary: { total_alcance: number; avg_engagement_rate: number; total_posts: number; best_score: number | null };
        metricas: Metrica[];
        publicaciones: Publicacion[];
      }>('/social-ops/metrics');
      setSource(res.source);
      setMetricas(res.metricas || []);
      setPublicaciones(res.publicaciones || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar métricas');
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
        : '0.00';
    const bestScore = metricas.length > 0 ? Math.max(...metricas.map((m) => m.score ?? 0)) : 0;
    const totalPosts = publicaciones.length > 0 ? publicaciones.length : new Set(metricas.map((m) => m.pub_id)).size;
    return { totalAlcance, avgEngagement, bestScore, totalPosts };
  }, [metricas, publicaciones]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-blue-900/30 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-blue-900/30 rounded-xl animate-pulse" />
      </div>
    );
  }

  const empty = metricas.length === 0 && publicaciones.length === 0;

  if (empty) {
    return (
      <div className="space-y-6">
        {error && (
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-rose-200 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Alcance Total', value: '—', icon: '👁️', gradient: 'from-blue-500/20 to-primary/10' },
            { label: 'Engagement', value: '—', icon: '💬', gradient: 'from-purple-500/20 to-pink-500/10' },
            { label: 'Posts', value: '0', icon: '📝', gradient: 'from-emerald-500/20 to-green-500/10' },
            { label: 'Mejor Score', value: '—', icon: '🏆', gradient: 'from-amber-500/20 to-orange-500/10' },
          ].map((card) => (
            <div
              key={card.label}
              className={`bg-gradient-to-br ${card.gradient} border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{card.icon}</span>
                <span className="text-[11px] text-muted uppercase tracking-wider">{card.label}</span>
              </div>
              <p className="text-2xl font-bold text-muted">{card.value}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-center justify-center py-16 space-y-4 bg-blue-950/30 rounded-xl border border-blue-800/20">
          <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary/10 to-purple-500/10 border border-primary/10 flex items-center justify-center">
            <span className="text-5xl">📊</span>
          </div>
          <h3 className="text-lg font-semibold text-muted">Aún no hay métricas</h3>
          <p className="text-sm text-muted max-w-lg text-center leading-relaxed">
            Las métricas aparecerán aquí cuando se publique contenido y se sincronice desde integraciones (Meta/TikTok/LinkedIn)
            o se registre desde el core. Cada publicación se clasifica como Ganador, Promedio o Perdedor según su score.
          </p>
          <button
            onClick={async () => {
              try {
                setLoading(true);
                await api('/social-ops/metrics/simulate', { method: 'POST' });
                await load();
              } catch (e) {
                setError(e instanceof Error ? e.message : 'No se pudo simular métricas');
                setLoading(false);
              }
            }}
            className="mt-2 px-5 py-2 rounded-xl bg-primary-dim hover:bg-primary text-white text-sm font-semibold"
          >
            Simular métricas
          </button>
          <div className="flex gap-3 mt-2">
            <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-3 py-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-[10px] text-emerald-300">Score ≥ 70</span>
            </div>
            <div className="flex items-center gap-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-full px-3 py-1">
              <span className="w-2 h-2 rounded-full bg-yellow-400" />
              <span className="text-[10px] text-yellow-300">Score 40-69</span>
            </div>
            <div className="flex items-center gap-1.5 bg-red-500/10 border border-red-500/20 rounded-full px-3 py-1">
              <span className="w-2 h-2 rounded-full bg-red-400" />
              <span className="text-[10px] text-red-300">Score &lt; 40</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-rose-200 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-gradient-to-br from-blue-500/20 to-primary/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">👁️</span>
            <span className="text-[11px] text-muted uppercase tracking-wider">Alcance Total</span>
          </div>
          <p className="text-2xl font-bold text-primary">{computed.totalAlcance.toLocaleString('es-CO')}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">💬</span>
            <span className="text-[11px] text-muted uppercase tracking-wider">Engagement</span>
          </div>
          <p className="text-2xl font-bold text-purple-300">{computed.avgEngagement}%</p>
        </div>
        <div className="bg-gradient-to-br from-emerald-500/20 to-green-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">📝</span>
            <span className="text-[11px] text-muted uppercase tracking-wider">Posts</span>
          </div>
          <p className="text-2xl font-bold text-emerald-300">{computed.totalPosts}</p>
        </div>
        <div className="bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">🏆</span>
            <span className="text-[11px] text-muted uppercase tracking-wider">Mejor Score</span>
          </div>
          <p className="text-2xl font-bold text-amber-300">{computed.bestScore || '—'}</p>
        </div>
      </div>

      <div className="bg-blue-950/50 border border-blue-800/40 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-blue-800/30 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-muted">Detalle por Publicación</h3>
          <span className="text-[10px] uppercase tracking-widest text-muted">source: {source}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[11px] text-muted uppercase tracking-wider border-b border-blue-800/20">
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
                <tr key={m.id} className="border-b border-blue-800/10 hover:bg-blue-900/20 transition">
                  <td className="px-4 py-3 text-muted font-mono text-xs">{m.fecha_captura}</td>
                  <td className="px-4 py-3 text-right text-muted">{Number(m.alcance).toLocaleString('es-CO')}</td>
                  <td className="px-4 py-3 text-right text-muted">{m.reacciones}</td>
                  <td className="px-4 py-3 text-right text-muted">{m.comentarios}</td>
                  <td className="px-4 py-3 text-right text-muted">{m.compartidos}</td>
                  <td className="px-4 py-3 text-right text-primary font-semibold">
                    {Number(m.engagement_rate).toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right text-amber-300 font-bold">{m.score ?? '—'}</td>
                  <td className="px-4 py-3 text-center">
                    {m.clasificacion ? (
                      <span
                        className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${
                          CLASIFICACION_STYLES[m.clasificacion] || 'bg-white/5 text-muted border border-outline/40'
                        }`}
                      >
                        {clasificacionLabels[m.clasificacion] ?? m.clasificacion}
                      </span>
                    ) : (
                      <span className="text-gray-600">—</span>
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

