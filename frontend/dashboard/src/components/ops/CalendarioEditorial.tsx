import React, { useEffect, useState } from 'react';
import {
  fetchCalendario,
  type Calendario,
  type Pilar,
  PILAR_COLORS,
  PILAR_LABELS,
  STATUS_COLORS,
  FORMATO_ICONS,
} from '../../lib/supabaseOps';

const CalendarioEditorial: React.FC = () => {
  const [entries, setEntries] = useState<Calendario[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedSemana, setSelectedSemana] = useState<number>(1);

  useEffect(() => {
    loadCalendario();
  }, [selectedSemana]);

  const loadCalendario = async () => {
    setLoading(true);
    const data = await fetchCalendario(selectedSemana);
    setEntries(data);
    setLoading(false);
  };

  const getDayLabel = (dateStr: string): string => {
    const date = new Date(dateStr + 'T12:00:00');
    return date.toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric', month: 'short' });
  };

  const statusLabels: Record<string, string> = {
    PLANIFICADO: 'Planificado',
    EN_PRODUCCION: 'En Producción',
    DRAFT: 'Borrador',
    REVIEW: 'En Revisión',
    APPROVED: 'Aprobado',
    PUBLISHED: 'Publicado',
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-20 bg-blue-900/30 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/20 flex items-center justify-center text-4xl">
          📅
        </div>
        <h3 className="text-lg font-semibold text-gray-300">Calendario vacío</h3>
        <p className="text-sm text-gray-500 max-w-md text-center">
          No hay publicaciones planificadas para la semana {selectedSemana}. 
          Selecciona ideas desde el Kanban y agrégalas al calendario editorial.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Week Selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">Semana:</span>
        <div className="flex gap-1">
          {[1, 2, 3, 4].map((week) => (
            <button
              key={week}
              onClick={() => setSelectedSemana(week)}
              className={`px-4 py-1.5 text-sm rounded-lg transition-all duration-200 ${
                selectedSemana === week
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'bg-blue-900/30 text-gray-400 border border-blue-800/30 hover:bg-blue-900/50'
              }`}
            >
              S{week}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-500 ml-auto font-mono">{entries.length} posts planificados</span>
      </div>

      {/* Calendar Entries */}
      <div className="space-y-2">
        {entries.map((entry) => (
          <div
            key={entry.id}
            onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
            className="group bg-blue-950/50 border border-blue-800/40 rounded-xl overflow-hidden cursor-pointer hover:border-cyan-500/20 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5"
          >
            {/* Main Row */}
            <div className="flex items-center gap-4 p-4">
              {/* Date Column */}
              <div className="flex-shrink-0 w-20 text-center">
                <p className="text-xs font-semibold text-cyan-400 uppercase tracking-wide">
                  {getDayLabel(entry.fecha_publicacion)}
                </p>
              </div>

              {/* Divider */}
              <div className="w-px h-10 bg-blue-800/50" />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">
                  {entry.titulo_trabajo || 'Sin título'}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {entry.pilar && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${PILAR_COLORS[entry.pilar]}`}>
                      {PILAR_LABELS[entry.pilar]}
                    </span>
                  )}
                  {entry.formato && (
                    <span className="text-[10px] text-gray-400">
                      {FORMATO_ICONS[entry.formato]}
                    </span>
                  )}
                </div>
              </div>

              {/* Status */}
              <div className="flex-shrink-0">
                <span className={`text-[11px] font-medium px-3 py-1 rounded-full ${STATUS_COLORS[entry.status]}`}>
                  {statusLabels[entry.status] ?? entry.status}
                </span>
              </div>

              {/* Expand Arrow */}
              <span className={`text-gray-600 text-xs transition-transform duration-200 ${expandedId === entry.id ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </div>

            {/* Expanded Details */}
            {expandedId === entry.id && (
              <div className="border-t border-blue-800/30 bg-blue-900/20 p-4 space-y-2 animate-in slide-in-from-top-1">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 text-xs">Responsable</span>
                    <p className="text-gray-300">{entry.responsable}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">Formato</span>
                    <p className="text-gray-300">{entry.formato ? `${FORMATO_ICONS[entry.formato]} ${entry.formato.replace('_', ' ')}` : '—'}</p>
                  </div>
                </div>
                {entry.notas_editoriales && (
                  <div>
                    <span className="text-gray-500 text-xs">Notas Editoriales</span>
                    <p className="text-gray-400 text-sm mt-0.5">{entry.notas_editoriales}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CalendarioEditorial;
