import React, { useState, useEffect } from 'react';

interface Suggestion {
  id: string;
  suggested_copy: string;
  suggested_image_id?: string;
  suggested_platform: string;
  suggested_time?: string;
  reason: string;
  status: 'pending' | 'accepted' | 'rejected';
}

interface CampaignSuggestionsProps {
  campaignId: string;
  onSelectSuggestion?: (suggestion: Suggestion) => void;
}

const CampaignSuggestions: React.FC<CampaignSuggestionsProps> = ({
  campaignId,
  onSelectSuggestion,
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'accepted' | 'rejected'>('pending');

  const API_BASE = 'http://localhost:8080/api/v1/social-content-ops/content';

  // Load suggestions
  useEffect(() => {
    fetchSuggestions();
  }, [campaignId]);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const statusParam = filterStatus !== 'all' ? `?status=${filterStatus}` : '';
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}/suggestions${statusParam}`);

      if (!response.ok) throw new Error('Failed to fetch suggestions');

      const data = await response.json();
      setSuggestions(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar sugerencias';
      setError(message);
      // Fallback mock data
      setSuggestions([
        {
          id: '1',
          suggested_copy:
            '¿Sabías que los PyMEs pierden dinero por falta de claridad financiera? 📊\n\nCon Contexia Pulso Diario ves tus finanzas en tiempo real, no en 40 días.',
          suggested_platform: 'instagram',
          suggested_time: '14:00',
          reason: 'Educational content - Loss Aversion behavioral psychology',
          status: 'pending',
        },
        {
          id: '2',
          suggested_copy:
            'Dropshipper que ahorró 15 horas/mes en gestión fiscal con Contexia.\n\n¿Y si recuperaras ese tiempo para crecer tu negocio? 🚀',
          suggested_platform: 'facebook',
          suggested_time: '10:00',
          reason: 'Social proof - Real customer success story',
          status: 'pending',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptSuggestion = async (suggestionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/campaigns/${campaignId}/suggestions/${suggestionId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'accepted' }),
        }
      );

      if (!response.ok) throw new Error('Failed to accept suggestion');

      setSuggestions(
        suggestions.map((s) => (s.id === suggestionId ? { ...s, status: 'accepted' } : s))
      );
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al aceptar';
      setError(message);
    }
  };

  const handleRejectSuggestion = async (suggestionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/campaigns/${campaignId}/suggestions/${suggestionId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'rejected' }),
        }
      );

      if (!response.ok) throw new Error('Failed to reject suggestion');

      setSuggestions(
        suggestions.map((s) => (s.id === suggestionId ? { ...s, status: 'rejected' } : s))
      );
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al rechazar';
      setError(message);
    }
  };

  const filteredSuggestions =
    filterStatus === 'all'
      ? suggestions
      : suggestions.filter((s) => s.status === filterStatus);

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500 text-red-500 p-3 rounded text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-blue-800">
        {(['all', 'pending', 'accepted', 'rejected'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-4 py-2 text-sm transition ${
              filterStatus === status
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {status === 'all' && '📋 Todas'}
            {status === 'pending' && '⏳ Pendientes'}
            {status === 'accepted' && '✅ Aceptadas'}
            {status === 'rejected' && '❌ Rechazadas'}
          </button>
        ))}
      </div>

      {/* Suggestions List */}
      {loading ? (
        <div className="text-center py-8 text-gray-400">Cargando sugerencias...</div>
      ) : filteredSuggestions.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>No hay sugerencias en este estado</p>
          <p className="text-xs mt-2">
            {filterStatus === 'all'
              ? 'Configura el Business DNA para obtener sugerencias'
              : `Sin sugerencias ${filterStatus}`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredSuggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className={`rounded-lg p-4 border transition ${
                suggestion.status === 'accepted'
                  ? 'bg-green-950/20 border-green-800'
                  : suggestion.status === 'rejected'
                    ? 'bg-red-950/20 border-red-800'
                    : 'bg-blue-950 border-blue-800 hover:border-cyan-600'
              }`}
            >
              {/* Status Badge */}
              <div className="flex justify-between items-start mb-3">
                <span className="text-xs font-semibold text-cyan-400">
                  🎯 {suggestion.suggested_platform.toUpperCase()}
                </span>
                <span className={`text-xs px-2 py-1 rounded ${
                  suggestion.status === 'accepted'
                    ? 'bg-green-600 text-white'
                    : suggestion.status === 'rejected'
                      ? 'bg-red-600 text-white'
                      : 'bg-yellow-600 text-white'
                }`}>
                  {suggestion.status === 'pending' && '⏳ Pendiente'}
                  {suggestion.status === 'accepted' && '✅ Aceptada'}
                  {suggestion.status === 'rejected' && '❌ Rechazada'}
                </span>
              </div>

              {/* Copy Preview */}
              <div className="bg-black/30 rounded p-3 mb-3">
                <p className="text-sm text-gray-100 whitespace-pre-wrap">{suggestion.suggested_copy}</p>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-3 mb-4 text-xs">
                <div>
                  <p className="text-gray-400">Razón:</p>
                  <p className="text-cyan-300">{suggestion.reason}</p>
                </div>
                {suggestion.suggested_time && (
                  <div>
                    <p className="text-gray-400">Hora sugerida:</p>
                    <p className="text-cyan-300">{suggestion.suggested_time}</p>
                  </div>
                )}
              </div>

              {/* Actions */}
              {suggestion.status === 'pending' && (
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      handleAcceptSuggestion(suggestion.id);
                      onSelectSuggestion?.(suggestion);
                    }}
                    className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition"
                  >
                    ✅ Aceptar
                  </button>
                  <button
                    onClick={() => handleRejectSuggestion(suggestion.id)}
                    className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition"
                  >
                    ❌ Rechazar
                  </button>
                </div>
              )}

              {suggestion.status === 'accepted' && (
                <button
                  onClick={() => onSelectSuggestion?.(suggestion)}
                  className="w-full px-3 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded transition"
                >
                  📝 Usar en Post Editor
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Generate New Suggestions (placeholder) */}
      <div className="bg-blue-950 rounded-lg p-4 border border-blue-800">
        <p className="text-sm text-gray-300 mb-3">
          💡 Sugerencias basadas en tu Business DNA. Acepta para usar en el editor.
        </p>
        <button
          onClick={fetchSuggestions}
          className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded transition"
        >
          🔄 Recargar Sugerencias
        </button>
      </div>
    </div>
  );
};

export default CampaignSuggestions;
