"use client";

import { useEffect, useMemo, useState } from "react";
import {
  getSocialOpsIdeas,
  updateSocialOpsIdeaStatus,
  generateSocialOpsIdeaDraft,
  type Idea,
  type IdeaStatus,
} from "@/lib/social-ops-api";

const COLUMNS: { id: IdeaStatus; label: string }[] = [
  { id: "NUEVA", label: "Nuevas" },
  { id: "SELECCIONADA", label: "Seleccionadas" },
  { id: "USADA", label: "Usadas" },
  { id: "DESCARTADA", label: "Descartadas" },
];

export function IdeasTab() {
  const [items, setItems] = useState<Idea[]>([]);
  const [source, setSource] = useState<"supabase" | "demo_fallback">("demo_fallback");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [draftText, setDraftText] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await getSocialOpsIdeas();
      setItems(res.items || []);
      setSource(res.source);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar ideas");
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
    setError("");
    setBusyId(ideaId);
    try {
      await updateSocialOpsIdeaStatus(ideaId, status);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo actualizar estado");
    } finally {
      setBusyId(null);
    }
  };

  const generate = async (idea: Idea) => {
    setError("");
    setBusyId(idea.id);
    setDraftText("");
    try {
      const res = await generateSocialOpsIdeaDraft(idea.id);
      setDraftText(res.draft_text || "");
      await move(idea.id, "USADA");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar borrador");
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
        Cargando ideas…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-4 text-status-critical text-sm">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant">Ideas</p>
          <p className="text-sm text-on-surface-variant">
            Fuente: <span className="text-on-surface">{source}</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {COLUMNS.map((col) => (
          <div key={col.id} className="rounded-xl border border-outline-variant/30 bg-surface-container p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-on-surface">{col.label}</p>
              <span className="text-xs text-on-surface-variant">{(grouped.get(col.id) || []).length}</span>
            </div>
            <div className="mt-3 space-y-2 min-h-10">
              {(grouped.get(col.id) || []).map((idea) => (
                <div key={idea.id} className="rounded-xl border border-outline-variant/30 bg-surface-elevated p-3">
                  <p className="text-sm text-on-surface leading-snug">{idea.tema_raw}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-on-surface-variant">
                    {idea.pilar && (
                      <span className="rounded-md border border-outline-variant/30 bg-white/5 px-2 py-0.5">{idea.pilar}</span>
                    )}
                    {idea.formato_sugerido && (
                      <span className="rounded-md border border-outline-variant/30 bg-white/5 px-2 py-0.5">
                        {idea.formato_sugerido}
                      </span>
                    )}
                    {typeof idea.score_potencial === "number" && (
                      <span className="rounded-md border border-outline-variant/30 bg-white/5 px-2 py-0.5">
                        {idea.score_potencial}/10
                      </span>
                    )}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {idea.status === "SELECCIONADA" ? (
                      <button
                        disabled={busyId === idea.id}
                        onClick={() => generate(idea)}
                        className="col-span-2 rounded-lg bg-primary text-on-primary py-2 text-xs font-bold hover:bg-primary-fixed-dim disabled:opacity-50"
                      >
                        Generar IA
                      </button>
                    ) : null}
                    {idea.status !== "SELECCIONADA" && (
                      <button
                        disabled={busyId === idea.id}
                        onClick={() => move(idea.id, "SELECCIONADA")}
                        className="rounded-lg border border-status-warning/40 bg-status-warning/10 py-2 text-xs font-semibold text-status-warning hover:bg-status-warning/15 disabled:opacity-50"
                      >
                        Seleccionar
                      </button>
                    )}
                    <button
                      disabled={busyId === idea.id}
                      onClick={() => move(idea.id, "DESCARTADA")}
                      className="rounded-lg border border-status-critical/40 bg-status-critical/10 py-2 text-xs font-semibold text-status-critical hover:bg-status-critical/15 disabled:opacity-50"
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
        <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-4">
          <p className="text-sm font-semibold text-on-surface">Borrador generado</p>
          <pre className="mt-3 whitespace-pre-wrap text-sm text-on-surface leading-6 font-sans">{draftText}</pre>
        </div>
      )}
    </div>
  );
}
