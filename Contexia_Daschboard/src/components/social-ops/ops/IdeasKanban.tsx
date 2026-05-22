import React, { useEffect, useState } from 'react';
import {
  fetchIdeas,
  updateIdeaStatus,
  type Idea,
  type IdeaStatus,
  type Pilar,
  PILAR_COLORS,
  PILAR_LABELS,
  FORMATO_ICONS,
} from '../../../lib/supabaseOps';

const COLUMNS: { status: IdeaStatus; label: string; color: string; icon: string }[] = [
  { status: 'NUEVA', label: 'Nuevas', color: 'from-blue-500/20 to-blue-600/10', icon: '✨' },
  { status: 'SELECCIONADA', label: 'Seleccionadas', color: 'from-amber-500/20 to-amber-600/10', icon: '⭐' },
  { status: 'USADA', label: 'Usadas', color: 'from-emerald-500/20 to-emerald-600/10', icon: '✅' },
  { status: 'DESCARTADA', label: 'Descartadas', color: 'from-red-500/20 to-red-600/10', icon: '🗑️' },
];

const IdeasKanban: React.FC = () => {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [movingId, setMovingId] = useState<number | null>(null);

  useEffect(() => {
    loadIdeas();
  }, []);

  const loadIdeas = async () => {
    setLoading(true);
    const data = await fetchIdeas();
    setIdeas(data);
    setLoading(false);
  };

  const handleMove = async (id: number, newStatus: IdeaStatus) => {
    setMovingId(id);
    const success = await updateIdeaStatus(id, newStatus);
    if (success) {
      setIdeas((prev) =>
        prev.map((idea) => (idea.id === id ? { ...idea, status: newStatus } : idea))
      );
    }
    setMovingId(null);
  };

  const handleGenerateAI = async (idea: Idea) => {
    try {
      setMovingId(idea.id); // Reusar state de loading
      // Llamar al backend de FastAPI
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea_id: String(idea.id), idea_text: idea.tema_raw })
      });
      
      if (!response.ok) throw new Error("Error en la IA");
      
      // Si la IA generó el borrador, pasamos la idea a USADA
      await handleMove(idea.id, 'USADA');
      alert('¡Borrador generado con éxito! Revisa la pestaña de Borradores.');
    } catch (err) {
      console.error("Error generando borrador:", err);
      alert('Hubo un error al conectar con el backend de IA.');
    } finally {
      setMovingId(null);
    }
  };

  const getIdeasByStatus = (status: IdeaStatus) =>
    ideas.filter((idea) => idea.status === status);

  const getNextStatuses = (current: IdeaStatus): IdeaStatus[] => {
    const map: Record<IdeaStatus, IdeaStatus[]> = {
      NUEVA: ['SELECCIONADA', 'DESCARTADA'],
      SELECCIONADA: ['USADA', 'NUEVA'],
      USADA: ['NUEVA'],
      DESCARTADA: ['NUEVA'],
    };
    return map[current] ?? [];
  };

  const statusActionLabels: Record<IdeaStatus, string> = {
    NUEVA: '← Devolver',
    SELECCIONADA: '⭐ Seleccionar',
    USADA: '✅ Marcar Usada',
    DESCARTADA: '🗑️ Descartar',
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-blue-950/50 border border-blue-800/50 rounded-xl p-4 space-y-3">
            <div className="h-6 bg-blue-800/50 rounded animate-pulse w-2/3" />
            {[1, 2, 3].map((j) => (
              <div key={j} className="h-28 bg-blue-900/30 rounded-lg animate-pulse" />
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (ideas.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/20 flex items-center justify-center text-4xl">
          💡
        </div>
        <h3 className="text-lg font-semibold text-gray-300">Sin ideas todavía</h3>
        <p className="text-sm text-gray-500 max-w-md text-center">
          El backlog está vacío. Ejecuta el workflow <span className="text-cyan-400 font-mono text-xs">WF-01-intake-ideas</span> en n8n para sembrar las primeras ideas, o ejecuta el SQL de semillas en Supabase.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {COLUMNS.map((col) => {
        const colIdeas = getIdeasByStatus(col.status);
        return (
          <div key={col.status} className="space-y-3">
            {/* Column Header */}
            <div className={`bg-gradient-to-r ${col.color} border border-blue-800/50 rounded-xl px-4 py-3 backdrop-blur-sm`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span>{col.icon}</span>
                  <span className="text-sm font-semibold text-gray-200">{col.label}</span>
                </div>
                <span className="text-xs font-mono text-gray-400 bg-blue-900/50 px-2 py-0.5 rounded-full">
                  {colIdeas.length}
                </span>
              </div>
            </div>

            {/* Cards */}
            <div className="space-y-2 min-h-[100px]">
              {colIdeas.map((idea) => (
                <div
                  key={idea.id}
                  className={`group bg-blue-950/60 border border-blue-800/40 rounded-xl p-4 hover:border-cyan-500/30 hover:bg-blue-950/80 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5 ${
                    movingId === idea.id ? 'opacity-50 scale-95' : ''
                  }`}
                >
                  {/* Title */}
                  <p className="text-sm font-medium text-gray-200 leading-snug mb-2.5 line-clamp-2">
                    {idea.tema_raw}
                  </p>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {idea.pilar && (
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${PILAR_COLORS[idea.pilar]}`}>
                        {PILAR_LABELS[idea.pilar]}
                      </span>
                    )}
                    {idea.formato_sugerido && (
                      <span className="text-[10px] bg-blue-800/40 text-gray-300 px-2 py-0.5 rounded-full">
                        {FORMATO_ICONS[idea.formato_sugerido]} {idea.formato_sugerido.replace('_', ' ')}
                      </span>
                    )}
                  </div>

                  {/* Score */}
                  {idea.score_potencial && (
                    <div className="flex items-center gap-1.5 mb-3">
                      <div className="flex gap-0.5">
                        {[...Array(5)].map((_, i) => (
                          <span
                            key={i}
                            className={`text-[10px] ${
                              i < Math.ceil(idea.score_potencial! / 2)
                                ? 'text-amber-400'
                                : 'text-gray-700'
                            }`}
                          >
                            ★
                          </span>
                        ))}
                      </div>
                      <span className="text-[10px] text-gray-500 font-mono">{idea.score_potencial}/10</span>
                    </div>
                  )}

                  {/* Dolor Tag */}
                  {idea.dolor_icp && (
                    <div className="mb-3">
                      <span className="text-[10px] text-red-400/70 bg-red-500/10 px-2 py-0.5 rounded">
                        🎯 {idea.dolor_icp.replace('_', ' ')}
                      </span>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    {idea.status === 'SELECCIONADA' && (
                      <button
                        onClick={() => handleGenerateAI(idea)}
                        disabled={movingId === idea.id}
                        className="flex-1 text-[10px] px-2 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold shadow shadow-cyan-500/20 transition-all duration-200"
                      >
                        {movingId === idea.id ? '⏳' : '🤖 Generar IA'}
                      </button>
                    )}
                    {getNextStatuses(idea.status).map((nextStatus) => (
                      <button
                        key={nextStatus}
                        onClick={() => handleMove(idea.id, nextStatus)}
                        disabled={movingId === idea.id}
                        className="flex-1 text-[10px] px-2 py-1.5 rounded-lg bg-blue-900/50 hover:bg-cyan-600/30 text-gray-300 hover:text-cyan-300 border border-blue-800/30 hover:border-cyan-500/30 transition-all duration-200"
                      >
                        {statusActionLabels[nextStatus]}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default IdeasKanban;
