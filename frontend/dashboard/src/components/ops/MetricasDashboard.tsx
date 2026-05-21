import React, { useEffect, useState } from 'react';
import {
  fetchMetricas,
  fetchPublicaciones,
  type Metrica,
  type Publicacion,
  CLASIFICACION_STYLES,
} from '../../lib/supabaseOps';

const MetricasDashboard: React.FC = () => {
  const [metricas, setMetricas] = useState<Metrica[]>([]);
  const [publicaciones, setPublicaciones] = useState<Publicacion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [met, pubs] = await Promise.all([fetchMetricas(), fetchPublicaciones()]);
    setMetricas(met);
    setPublicaciones(pubs);
    setLoading(false);
  };

  // Computed Metrics
  const totalAlcance = metricas.reduce((sum, m) => sum + m.alcance, 0);
  const avgEngagement = metricas.length > 0
    ? (metricas.reduce((sum, m) => sum + Number(m.engagement_rate), 0) / metricas.length).toFixed(2)
    : '0.00';
  const bestScore = metricas.length > 0
    ? Math.max(...metricas.map((m) => m.score ?? 0))
    : 0;
  const totalPosts = publicaciones.length;

  const clasificacionLabels: Record<string, string> = {
    GANADOR: '🏆 Ganador',
    PROMEDIO: '📊 Promedio',
    PERDEDOR: '📉 Perdedor',
  };

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

  if (metricas.length === 0 && publicaciones.length === 0) {
    return (
      <div className="space-y-6">
        {/* Summary Cards (Empty State) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Alcance Total', value: '—', icon: '👁️', gradient: 'from-blue-500/20 to-cyan-500/10' },
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
                <span className="text-[11px] text-gray-400 uppercase tracking-wider">{card.label}</span>
              </div>
              <p className="text-2xl font-bold text-gray-300">{card.value}</p>
            </div>
          ))}
        </div>

        {/* Empty State */}
        <div className="flex flex-col items-center justify-center py-16 space-y-4 bg-blue-950/30 rounded-xl border border-blue-800/20">
          <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-purple-500/10 border border-cyan-500/10 flex items-center justify-center">
            <span className="text-5xl">📊</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-300">Aún no hay métricas</h3>
          <p className="text-sm text-gray-500 max-w-lg text-center leading-relaxed">
            Las métricas aparecerán aquí cuando se publique contenido y se ejecute el workflow 
            <span className="text-cyan-400 font-mono text-xs"> WF-08-captura-metricas</span>.
            Cada publicación será analizada con un score de engagement y clasificada como
            <span className="text-emerald-400"> Ganador</span>,
            <span className="text-yellow-400"> Promedio</span> o
            <span className="text-red-400"> Perdedor</span>.
          </p>
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
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">👁️</span>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider">Alcance Total</span>
          </div>
          <p className="text-2xl font-bold text-cyan-300">{totalAlcance.toLocaleString('es-CO')}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">💬</span>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider">Engagement</span>
          </div>
          <p className="text-2xl font-bold text-purple-300">{avgEngagement}%</p>
        </div>
        <div className="bg-gradient-to-br from-emerald-500/20 to-green-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">📝</span>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider">Posts</span>
          </div>
          <p className="text-2xl font-bold text-emerald-300">{totalPosts}</p>
        </div>
        <div className="bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-blue-800/30 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">🏆</span>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider">Mejor Score</span>
          </div>
          <p className="text-2xl font-bold text-amber-300">{bestScore}</p>
        </div>
      </div>

      {/* Metrics Table */}
      <div className="bg-blue-950/50 border border-blue-800/40 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-blue-800/30">
          <h3 className="text-sm font-semibold text-gray-300">Detalle por Publicación</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[11px] text-gray-500 uppercase tracking-wider border-b border-blue-800/20">
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
                  <td className="px-4 py-3 text-gray-300 font-mono text-xs">{m.fecha_captura}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{m.alcance.toLocaleString('es-CO')}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{m.reacciones}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{m.comentarios}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{m.compartidos}</td>
                  <td className="px-4 py-3 text-right text-cyan-300 font-semibold">{Number(m.engagement_rate).toFixed(2)}%</td>
                  <td className="px-4 py-3 text-right text-amber-300 font-bold">{m.score ?? '—'}</td>
                  <td className="px-4 py-3 text-center">
                    {m.clasificacion ? (
                      <span className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${CLASIFICACION_STYLES[m.clasificacion]}`}>
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
};

export default MetricasDashboard;
