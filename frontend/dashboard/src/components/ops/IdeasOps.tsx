import React, { useEffect, useMemo, useState } from 'react';
import { simulateSocialOpsEvent } from '../../lib/socialOpsApi';

type IdeaStatus = 'NUEVA' | 'SELECCIONADA' | 'USADA' | 'DESCARTADA';

type Idea = {
  id: number;
  tema_raw: string;
  pilar?: string | null;
  formato_sugerido?: string | null;
  status: IdeaStatus;
  score_potencial?: number | null;
};

const COLUMNS: Array<{ id: IdeaStatus; label: string }> = [
  { id: 'NUEVA', label: 'Nuevas' },
  { id: 'SELECCIONADA', label: 'Seleccionadas' },
  { id: 'USADA', label: 'Usadas' },
  { id: 'DESCARTADA', label: 'Descartadas' },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
  const resp = await fetch(`${base}${path}`, {
    ...init,
    headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...(init?.headers || {}) },
  });
  if (!resp.ok) throw new Error(await resp.text());
  return (await resp.json()) as T;
}

export default function IdeasOps() {
  const [items, setItems] = useState<Idea[]>([]);
  const [source, setSource] = useState<'supabase' | 'demo_fallback'>('demo_fallback');
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [draftText, setDraftText] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await api<{ source: 'supabase' | 'demo_fallback'; items: Idea[] }>('/social-ops/ideas');
      setItems(res.items || []);
      setSource(res.source);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar ideas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<IdeaStatus, Idea[]>();
    COLUMNS.forEach((col) => map.set(col.id, []));
    items.forEach((idea) => map.get(idea.status)?.push(idea));
    return map;
  }, [items]);

  const move = async (ideaId: number, status: IdeaStatus) => {
    setError('');
    setBusyId(ideaId);
    try {
      await api(`/social-ops/ideas/${ideaId}/status`, { method: 'POST', body: JSON.stringify({ status }) });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo actualizar estado');
    } finally {
      setBusyId(null);
    }
  };

  const generate = async (idea: Idea) => {
    setError('');
    setBusyId(idea.id);
    setDraftText('');
    try {
      const res = await api<{ idea_id: number; draft_text: string }>(`/social-ops/ideas/${idea.id}/generate-draft`, {
        method: 'POST',
      });
      setDraftText(res.draft_text || '');
      await move(idea.id, 'USADA');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo generar borrador');
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return <div className="rounded-xl border border-outline/40 bg-white/5 p-6 text-muted">Cargando ideas…</div>;
  }

  return (
    <div className="space-y-4">
      {error && <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-rose-200">{error}</div>}

      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted">Ideas</p>
          <p className="text-sm text-muted">
            Fuente: <span className="text-ink">{source}</span>
          </p>
        </div>
        <button
          onClick={() =>
            simulateSocialOpsEvent({
              channel: 'instagram',
              event_type: 'comment',
              actor_handle: '@ops_seed',
              text: 'Sembrar nuevas ideas para la semana',
            }).catch(() => null)
          }
          className="rounded-xl border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary hover:bg-primary/15"
        >
          Sembrar (demo)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {COLUMNS.map((col) => (
          <div key={col.id} className="rounded-xl border border-outline/40 bg-white/5 p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-white">{col.label}</p>
              <span className="text-xs text-muted">{(grouped.get(col.id) || []).length}</span>
            </div>
            <div className="mt-3 space-y-2 min-h-10">
              {(grouped.get(col.id) || []).map((idea) => (
                <div key={idea.id} className="rounded-xl border border-outline/40 bg-slate-950/60 p-3">
                  <p className="text-sm text-ink leading-snug">{idea.tema_raw}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted">
                    {idea.pilar && <span className="rounded-md border border-outline/40 bg-white/5 px-2 py-0.5">{idea.pilar}</span>}
                    {idea.formato_sugerido && (
                      <span className="rounded-md border border-outline/40 bg-white/5 px-2 py-0.5">{idea.formato_sugerido}</span>
                    )}
                    {typeof idea.score_potencial === 'number' && (
                      <span className="rounded-md border border-outline/40 bg-white/5 px-2 py-0.5">{idea.score_potencial}/10</span>
                    )}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {idea.status === 'SELECCIONADA' ? (
                      <button
                        disabled={busyId === idea.id}
                        onClick={() => generate(idea)}
                        className="col-span-2 rounded-lg bg-primary text-obsidian py-2 text-xs font-bold hover:bg-primary-dim disabled:opacity-50"
                      >
                        Generar IA
                      </button>
                    ) : null}
                    {idea.status !== 'SELECCIONADA' && (
                      <button
                        disabled={busyId === idea.id}
                        onClick={() => move(idea.id, 'SELECCIONADA')}
                        className="rounded-lg border border-amber-500/40 bg-amber-500/10 py-2 text-xs font-semibold text-amber-200 hover:bg-amber-500/15 disabled:opacity-50"
                      >
                        Seleccionar
                      </button>
                    )}
                    <button
                      disabled={busyId === idea.id}
                      onClick={() => move(idea.id, 'DESCARTADA')}
                      className="rounded-lg border border-rose-500/40 bg-rose-500/10 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-500/15 disabled:opacity-50"
                    >
                      Descartar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {draftText && (
        <div className="rounded-xl border border-outline/40 bg-white/5 p-4">
          <p className="text-sm font-semibold text-white">Borrador generado</p>
          <pre className="mt-3 whitespace-pre-wrap text-sm text-ink leading-6">{draftText}</pre>
        </div>
      )}
    </div>
  );
}

