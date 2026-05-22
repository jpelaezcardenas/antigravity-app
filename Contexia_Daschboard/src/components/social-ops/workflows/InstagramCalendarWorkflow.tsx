import React, { useState, useEffect } from 'react';

interface Post {
  fecha: string;
  hora: string;
  dia_semana: string;
  semana: number;
  pillar: string;
  post: {
    titulo: string;
    contenido: string;
    emoji: string;
    hashtags: string[];
    cta: string;
  };
}

interface CalendarData {
  campaign_objective: string;
  start_date: string;
  total_posts: number;
  weeks: number;
  posts_per_week: number;
  posts: Post[];
  metrics: {
    expected_reach: number;
    expected_engagement: number;
    expected_engagement_rate: string;
    expected_ctr: string;
    posts_per_pillar: Record<string, number>;
  };
  pillar_rotation: string[];
}

interface InstagramCalendarWorkflowProps {
  campaignId: string;
  campaignObjective: string;
  businessDna?: any;
}

const PILLAR_COLORS = {
  regulatorio: { bg: 'bg-red-950', border: 'border-red-800', text: 'text-red-400', icon: '📋' },
  educativo: { bg: 'bg-blue-950', border: 'border-blue-800', text: 'text-blue-400', icon: '📚' },
  comercial: { bg: 'bg-yellow-950', border: 'border-yellow-800', text: 'text-yellow-400', icon: '💰' },
  social_proof: { bg: 'bg-purple-950', border: 'border-purple-800', text: 'text-purple-400', icon: '⭐' }
};

const InstagramCalendarWorkflow: React.FC<InstagramCalendarWorkflowProps> = ({
  campaignId,
  campaignObjective,
  businessDna
}) => {
  const [calendar, setCalendar] = useState<CalendarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [weeks, setWeeks] = useState(4);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    generateCalendar();
  }, [weeks]);

  const generateCalendar = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/social-content-ops/workflows/instagram-calendar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          campaign_objective: campaignObjective,
          business_dna: businessDna || {},
          weeks: weeks,
          posts_per_week: 4
        })
      });

      if (!response.ok) throw new Error('Failed to generate calendar');
      const data = await response.json();
      setCalendar(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      // Mock data fallback
      setCalendar(getMockCalendar());
    } finally {
      setLoading(false);
    }
  };

  const getMockCalendar = (): CalendarData => {
    return {
      campaign_objective: campaignObjective,
      start_date: new Date().toISOString().split('T')[0],
      total_posts: 16,
      weeks: 4,
      posts_per_week: 4,
      posts: [
        {
          fecha: '2026-05-19',
          hora: '10:00',
          dia_semana: 'Lunes',
          semana: 1,
          pillar: 'regulatorio',
          post: {
            titulo: '📋 Actualización Regulatoria',
            contenido: 'Tu declaración de renta 2025 vence en X días. ¿Tienes todos los documentos listos?',
            emoji: '📋',
            hashtags: ['#fiscal', '#DIAN', '#cumplimiento'],
            cta: 'Agenda tu asesoría →'
          }
        }
      ],
      metrics: {
        expected_reach: 4800,
        expected_engagement: 240,
        expected_engagement_rate: '5.0%',
        expected_ctr: '2-4%',
        posts_per_pillar: {
          regulatorio: 4,
          educativo: 4,
          comercial: 4,
          social_proof: 4
        }
      },
      pillar_rotation: ['regulatorio', 'educativo', 'comercial', 'social_proof']
    };
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-400">Generando calendario...</div>;
  }

  if (error && !calendar) {
    return <div className="text-center py-8 text-red-400">Error: {error}</div>;
  }

  if (!calendar) {
    return <div className="text-center py-8 text-gray-400">Sin datos disponibles</div>;
  }

  const groupedByWeek = calendar.posts.reduce((acc, post) => {
    if (!acc[post.semana]) acc[post.semana] = [];
    acc[post.semana].push(post);
    return acc;
  }, {} as Record<number, Post[]>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-cyan-400 mb-2">📅 Instagram Calendar Workflow</h2>
        <p className="text-gray-400 mb-4">{campaignObjective}</p>

        <div className="flex gap-4 items-center mb-4">
          <label className="text-gray-300">Semanas a generar:</label>
          <select
            value={weeks}
            onChange={(e) => setWeeks(parseInt(e.target.value))}
            className="bg-blue-900 border border-blue-700 text-white rounded px-3 py-2"
          >
            <option value={2}>2 semanas</option>
            <option value={4}>4 semanas</option>
            <option value={6}>6 semanas</option>
          </select>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-4 gap-2 text-sm">
          {calendar.pillar_rotation.map((pillar) => {
            const colors = PILLAR_COLORS[pillar as keyof typeof PILLAR_COLORS];
            return (
              <div key={pillar} className={`${colors.bg} ${colors.border} border rounded p-2`}>
                <span className={colors.text}>{colors.icon} {pillar.charAt(0).toUpperCase() + pillar.slice(1)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Calendar Grid by Week */}
      <div className="space-y-4">
        {Object.entries(groupedByWeek).map(([weekNum, weekPosts]) => (
          <div key={weekNum} className="bg-blue-950 border border-blue-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-cyan-400 mb-4">📆 Semana {weekNum}</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {weekPosts.map((post, idx) => {
                const colors = PILLAR_COLORS[post.pillar as keyof typeof PILLAR_COLORS];
                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedPost(post)}
                    className={`${colors.bg} ${colors.border} border rounded-lg p-4 cursor-pointer hover:shadow-lg transition transform hover:scale-105`}
                  >
                    <div className={`${colors.text} font-bold text-sm mb-2`}>
                      {post.fecha} - {post.hora}
                    </div>
                    <div className="text-white text-sm font-semibold mb-2 line-clamp-2">
                      {post.post.titulo}
                    </div>
                    <div className="text-xs text-gray-300 line-clamp-2 mb-2">
                      {post.post.contenido}
                    </div>
                    <div className={`text-xs ${colors.text}`}>
                      {post.dia_semana} • {post.pillar}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Metrics Panel */}
      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-cyan-400 mb-4">📊 Métricas Esperadas</h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-900 rounded p-4 text-center">
            <div className="text-2xl font-bold text-cyan-400">{calendar.total_posts}</div>
            <div className="text-xs text-gray-400">Total Posts</div>
          </div>

          <div className="bg-blue-900 rounded p-4 text-center">
            <div className="text-2xl font-bold text-green-400">{calendar.metrics.expected_reach.toLocaleString()}</div>
            <div className="text-xs text-gray-400">Reach Esperado</div>
          </div>

          <div className="bg-blue-900 rounded p-4 text-center">
            <div className="text-2xl font-bold text-yellow-400">{calendar.metrics.expected_engagement}</div>
            <div className="text-xs text-gray-400">Engagement Total</div>
          </div>

          <div className="bg-blue-900 rounded p-4 text-center">
            <div className="text-2xl font-bold text-purple-400">{calendar.metrics.expected_engagement_rate}</div>
            <div className="text-xs text-gray-400">Tasa de Engagement</div>
          </div>
        </div>

        {/* Posts by Pillar */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(calendar.metrics.posts_per_pillar).map(([pillar, count]) => {
            const colors = PILLAR_COLORS[pillar as keyof typeof PILLAR_COLORS];
            return (
              <div
                key={pillar}
                className={`${colors.bg} ${colors.border} border rounded p-4 text-center`}
              >
                <div className={`text-xl font-bold ${colors.text}`}>{count}</div>
                <div className={`text-xs ${colors.text}`}>{pillar}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Post Detail Modal */}
      {selectedPost && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-blue-950 border border-blue-800 rounded-lg p-8 max-w-2xl w-full max-h-96 overflow-y-auto">
            <button
              onClick={() => setSelectedPost(null)}
              className="float-right text-cyan-400 hover:text-cyan-300 text-2xl"
            >
              ✕
            </button>

            <h3 className="text-2xl font-bold text-cyan-400 mb-4">{selectedPost.post.titulo}</h3>

            <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
              <div>
                <span className="text-gray-400">Fecha:</span>
                <div className="text-white font-semibold">{selectedPost.fecha}</div>
              </div>
              <div>
                <span className="text-gray-400">Hora:</span>
                <div className="text-white font-semibold">{selectedPost.hora}</div>
              </div>
              <div>
                <span className="text-gray-400">Día:</span>
                <div className="text-white font-semibold">{selectedPost.dia_semana}</div>
              </div>
              <div>
                <span className="text-gray-400">Pillar:</span>
                <div className="text-white font-semibold capitalize">{selectedPost.pillar}</div>
              </div>
            </div>

            <div className="bg-blue-900 rounded p-4 mb-4">
              <p className="text-white text-sm leading-relaxed">{selectedPost.post.contenido}</p>
            </div>

            <div className="mb-4">
              <span className="text-gray-400 text-sm">Hashtags:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {selectedPost.post.hashtags.map((tag, idx) => (
                  <span key={idx} className="bg-cyan-600 text-white text-xs rounded-full px-3 py-1">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded p-4 text-white text-center font-semibold">
              {selectedPost.post.cta}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstagramCalendarWorkflow;
