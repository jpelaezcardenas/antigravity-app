import React, { useEffect, useState } from 'react';
import {
  fetchBorradores,
  aprobarContenido,
  updateContenido,
  type Contenido,
} from '../../../lib/supabaseOps';

const BorradoresReview: React.FC = () => {
  const [borradores, setBorradores] = useState<Contenido[]>([]);
  const [loading, setLoading] = useState(true);
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState<Partial<Contenido>>({});

  useEffect(() => {
    loadBorradores();
  }, []);

  const loadBorradores = async () => {
    setLoading(true);
    const data = await fetchBorradores();
    setBorradores(data);
    setLoading(false);
  };

  const handleAprobar = async (id: number) => {
    setApprovingId(id);
    const success = await aprobarContenido(id);
    if (success) {
      setBorradores((prev) => prev.filter((b) => b.id !== id));
    }
    setApprovingId(null);
  };

  const handleEdit = (borrador: Contenido) => {
    setEditingId(borrador.id);
    setEditValues({
      hook: borrador.hook,
      copy_body: borrador.copy_body,
      cta: borrador.cta,
      hashtags: borrador.hashtags,
    });
  };

  const handleSaveEdit = async (id: number) => {
    const success = await updateContenido(id, { ...editValues, status: 'EDITADO_HUMANO' });
    if (success) {
      setBorradores((prev) =>
        prev.map((b) => (b.id === id ? { ...b, ...editValues, status: 'EDITADO_HUMANO' as const } : b))
      );
    }
    setEditingId(null);
    setEditValues({});
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      BORRADOR_IA: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
      EDITADO_HUMANO: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    };
    const labels: Record<string, string> = {
      BORRADOR_IA: '🤖 Borrador IA',
      EDITADO_HUMANO: '✍️ Editado',
    };
    return (
      <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full border ${styles[status] ?? ''}`}>
        {labels[status] ?? status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-blue-900/30 rounded-xl p-6 space-y-3 animate-pulse">
            <div className="h-5 bg-blue-800/50 rounded w-3/4" />
            <div className="h-24 bg-blue-800/30 rounded" />
            <div className="h-4 bg-blue-800/40 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (borradores.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/20 flex items-center justify-center text-4xl">
          ✅
        </div>
        <h3 className="text-lg font-semibold text-gray-300">Todo aprobado</h3>
        <p className="text-sm text-gray-500 max-w-md text-center">
          No hay borradores pendientes de revisión. Los nuevos borradores aparecerán aquí cuando el workflow 
          <span className="text-cyan-400 font-mono text-xs"> WF-04-draft-creator</span> genere contenido.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">
          <span className="text-cyan-400 font-semibold">{borradores.length}</span> borrador{borradores.length !== 1 ? 'es' : ''} pendiente{borradores.length !== 1 ? 's' : ''} de revisión
        </p>
      </div>

      {borradores.map((borrador) => (
        <div
          key={borrador.id}
          className="bg-blue-950/50 border border-blue-800/40 rounded-xl overflow-hidden transition-all duration-300 hover:border-cyan-500/20"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-blue-800/30">
            <div className="flex items-center gap-3">
              {statusBadge(borrador.status)}
              <span className="text-xs text-gray-500 font-mono">v{borrador.version}</span>
              {borrador.qa_humanizacion && (
                <span className="text-[10px] bg-green-500/20 text-green-300 px-2 py-0.5 rounded-full">
                  ✓ QA Humanización
                </span>
              )}
            </div>
            <span className="text-xs text-gray-600">ID #{borrador.id}</span>
          </div>

          {/* Content Preview */}
          <div className="p-5 space-y-4">
            {/* Hook Section */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">Hook Principal</label>
              {editingId === borrador.id ? (
                <textarea
                  value={editValues.hook ?? ''}
                  onChange={(e) => setEditValues({ ...editValues, hook: e.target.value })}
                  className="w-full mt-1 bg-blue-900/50 border border-blue-700 rounded-lg p-3 text-sm text-gray-200 focus:border-cyan-500/50 focus:outline-none resize-none"
                  rows={2}
                />
              ) : (
                <p className="text-base font-semibold text-cyan-300 mt-1 leading-relaxed">
                  {borrador.hook || '—'}
                </p>
              )}
            </div>

            {/* Hook Alternatives (collapsed) */}
            {(borrador.hook_alt_1 || borrador.hook_alt_2) && editingId !== borrador.id && (
              <div className="flex gap-2">
                {borrador.hook_alt_1 && (
                  <div className="flex-1 bg-blue-900/20 rounded-lg p-2.5 border border-blue-800/20">
                    <span className="text-[9px] text-gray-500 uppercase">Alt 1</span>
                    <p className="text-xs text-gray-400 mt-0.5">{borrador.hook_alt_1}</p>
                  </div>
                )}
                {borrador.hook_alt_2 && (
                  <div className="flex-1 bg-blue-900/20 rounded-lg p-2.5 border border-blue-800/20">
                    <span className="text-[9px] text-gray-500 uppercase">Alt 2</span>
                    <p className="text-xs text-gray-400 mt-0.5">{borrador.hook_alt_2}</p>
                  </div>
                )}
              </div>
            )}

            {/* Copy Body */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">Copy</label>
              {editingId === borrador.id ? (
                <textarea
                  value={editValues.copy_body ?? ''}
                  onChange={(e) => setEditValues({ ...editValues, copy_body: e.target.value })}
                  className="w-full mt-1 bg-blue-900/50 border border-blue-700 rounded-lg p-3 text-sm text-gray-200 focus:border-cyan-500/50 focus:outline-none resize-none"
                  rows={6}
                />
              ) : (
                <p className="text-sm text-gray-300 mt-1 leading-relaxed whitespace-pre-line">
                  {borrador.copy_body || '—'}
                </p>
              )}
            </div>

            {/* CTA + Hashtags */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">CTA</label>
                {editingId === borrador.id ? (
                  <input
                    value={editValues.cta ?? ''}
                    onChange={(e) => setEditValues({ ...editValues, cta: e.target.value })}
                    className="w-full mt-1 bg-blue-900/50 border border-blue-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:border-cyan-500/50 focus:outline-none"
                  />
                ) : (
                  <p className="text-sm text-emerald-300/80 mt-1 italic">{borrador.cta || '—'}</p>
                )}
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">Hashtags</label>
                {editingId === borrador.id ? (
                  <input
                    value={editValues.hashtags ?? ''}
                    onChange={(e) => setEditValues({ ...editValues, hashtags: e.target.value })}
                    className="w-full mt-1 bg-blue-900/50 border border-blue-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:border-cyan-500/50 focus:outline-none"
                  />
                ) : (
                  <p className="text-sm text-blue-400/70 mt-1">{borrador.hashtags || '—'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 p-4 border-t border-blue-800/30 bg-blue-900/10">
            {editingId === borrador.id ? (
              <>
                <button
                  onClick={() => { setEditingId(null); setEditValues({}); }}
                  className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => handleSaveEdit(borrador.id)}
                  className="px-5 py-2 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                  💾 Guardar Edición
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleEdit(borrador)}
                  className="px-4 py-2 text-sm text-gray-400 hover:text-cyan-300 border border-blue-800/30 hover:border-cyan-500/30 rounded-lg transition"
                >
                  ✏️ Editar
                </button>
                <button
                  onClick={() => handleAprobar(borrador.id)}
                  disabled={approvingId === borrador.id}
                  className={`px-5 py-2 text-sm font-semibold rounded-lg transition-all duration-300 ${
                    approvingId === borrador.id
                      ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30'
                  }`}
                >
                  {approvingId === borrador.id ? '⏳ Aprobando...' : '✅ Aprobar y Programar'}
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default BorradoresReview;
