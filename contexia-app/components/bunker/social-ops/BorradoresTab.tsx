"use client";

import { useEffect, useState } from "react";
import {
  getSocialOpsBorradores,
  approveSocialOpsBorrador,
  updateSocialOpsBorrador,
  type Contenido,
} from "@/lib/social-ops-api";

const STATUS_STYLES: Record<string, string> = {
  BORRADOR_IA: "bg-secondary/15 text-secondary-fixed border-secondary/30",
  EDITADO_HUMANO: "bg-primary/15 text-primary-container border-primary/30",
};

const STATUS_LABELS: Record<string, string> = {
  BORRADOR_IA: "Borrador IA",
  EDITADO_HUMANO: "Editado",
};

export function BorradoresTab() {
  const [borradores, setBorradores] = useState<Contenido[]>([]);
  const [loading, setLoading] = useState(true);
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState<Partial<Contenido>>({});

  const load = async () => {
    setLoading(true);
    try {
      const res = await getSocialOpsBorradores();
      setBorradores(res.items || []);
    } catch {
      setBorradores([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleAprobar = async (id: number) => {
    setApprovingId(id);
    try {
      await approveSocialOpsBorrador(id);
      setBorradores((prev) => prev.filter((b) => b.id !== id));
    } catch {
      // keep item visible on failure
    } finally {
      setApprovingId(null);
    }
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
    try {
      await updateSocialOpsBorrador(id, editValues);
      setBorradores((prev) =>
        prev.map((b) => (b.id === id ? { ...b, ...editValues, status: "EDITADO_HUMANO" as const } : b))
      );
    } catch {
      // keep prior values on failure
    }
    setEditingId(null);
    setEditValues({});
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-surface-container rounded-xl p-6 space-y-3 animate-pulse">
            <div className="h-5 bg-white/10 rounded w-3/4" />
            <div className="h-24 bg-white/5 rounded" />
            <div className="h-4 bg-white/10 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (borradores.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="w-20 h-20 rounded-2xl bg-status-success/10 border border-status-success/20 flex items-center justify-center">
          <span className="material-symbols-outlined text-4xl text-status-success">check_circle</span>
        </div>
        <h3 className="text-lg font-semibold text-on-surface-variant">Todo aprobado</h3>
        <p className="text-sm text-on-surface-variant max-w-md text-center">
          No hay borradores pendientes de revisión. Los nuevos borradores aparecerán aquí cuando el Content Idea
          Generator genere contenido.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-on-surface-variant">
        <span className="text-primary-container font-semibold">{borradores.length}</span> borrador
        {borradores.length !== 1 ? "es" : ""} pendiente{borradores.length !== 1 ? "s" : ""} de revisión
      </p>

      {borradores.map((borrador) => (
        <div
          key={borrador.id}
          className="bg-surface-elevated border border-outline-variant/20 rounded-xl overflow-hidden hover:border-primary/30 transition-all"
        >
          <div className="flex items-center justify-between p-4 border-b border-outline-variant/20">
            <div className="flex items-center gap-3">
              <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full border ${STATUS_STYLES[borrador.status] ?? ""}`}>
                {STATUS_LABELS[borrador.status] ?? borrador.status}
              </span>
              <span className="text-xs text-on-surface-variant font-mono">v{borrador.version}</span>
              {borrador.qa_humanizacion && (
                <span className="text-[10px] bg-status-success/15 text-status-success px-2 py-0.5 rounded-full">
                  QA Humanización
                </span>
              )}
            </div>
            <span className="text-xs text-on-surface-variant/60">ID #{borrador.id}</span>
          </div>

          <div className="p-5 space-y-4">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold">Hook Principal</label>
              {editingId === borrador.id ? (
                <textarea
                  value={editValues.hook ?? ""}
                  onChange={(e) => setEditValues({ ...editValues, hook: e.target.value })}
                  className="w-full mt-1 bg-surface-container border border-outline-variant/30 rounded-lg p-3 text-sm text-on-surface focus:border-primary/50 focus:outline-none resize-none"
                  rows={2}
                />
              ) : (
                <p className="text-base font-semibold text-primary-container mt-1 leading-relaxed">{borrador.hook || "—"}</p>
              )}
            </div>

            {(borrador.hook_alt_1 || borrador.hook_alt_2) && editingId !== borrador.id && (
              <div className="flex gap-2">
                {borrador.hook_alt_1 && (
                  <div className="flex-1 bg-surface-container rounded-lg p-2.5 border border-outline-variant/20">
                    <span className="text-[9px] text-on-surface-variant uppercase">Alt 1</span>
                    <p className="text-xs text-on-surface-variant mt-0.5">{borrador.hook_alt_1}</p>
                  </div>
                )}
                {borrador.hook_alt_2 && (
                  <div className="flex-1 bg-surface-container rounded-lg p-2.5 border border-outline-variant/20">
                    <span className="text-[9px] text-on-surface-variant uppercase">Alt 2</span>
                    <p className="text-xs text-on-surface-variant mt-0.5">{borrador.hook_alt_2}</p>
                  </div>
                )}
              </div>
            )}

            <div>
              <label className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold">Copy</label>
              {editingId === borrador.id ? (
                <textarea
                  value={editValues.copy_body ?? ""}
                  onChange={(e) => setEditValues({ ...editValues, copy_body: e.target.value })}
                  className="w-full mt-1 bg-surface-container border border-outline-variant/30 rounded-lg p-3 text-sm text-on-surface focus:border-primary/50 focus:outline-none resize-none"
                  rows={6}
                />
              ) : (
                <p className="text-sm text-on-surface-variant mt-1 leading-relaxed whitespace-pre-line">{borrador.copy_body || "—"}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold">CTA</label>
                {editingId === borrador.id ? (
                  <input
                    value={editValues.cta ?? ""}
                    onChange={(e) => setEditValues({ ...editValues, cta: e.target.value })}
                    className="w-full mt-1 bg-surface-container border border-outline-variant/30 rounded-lg px-3 py-2 text-sm text-on-surface focus:border-primary/50 focus:outline-none"
                  />
                ) : (
                  <p className="text-sm text-status-success/90 mt-1 italic">{borrador.cta || "—"}</p>
                )}
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold">Hashtags</label>
                {editingId === borrador.id ? (
                  <input
                    value={editValues.hashtags ?? ""}
                    onChange={(e) => setEditValues({ ...editValues, hashtags: e.target.value })}
                    className="w-full mt-1 bg-surface-container border border-outline-variant/30 rounded-lg px-3 py-2 text-sm text-on-surface focus:border-primary/50 focus:outline-none"
                  />
                ) : (
                  <p className="text-sm text-primary-container/80 mt-1">{borrador.hashtags || "—"}</p>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 p-4 border-t border-outline-variant/20 bg-white/5">
            {editingId === borrador.id ? (
              <>
                <button
                  onClick={() => {
                    setEditingId(null);
                    setEditValues({});
                  }}
                  className="px-4 py-2 text-sm text-on-surface-variant hover:text-on-surface transition"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => handleSaveEdit(borrador.id)}
                  className="px-5 py-2 text-sm font-semibold bg-primary hover:bg-primary-fixed-dim text-on-primary rounded-lg transition"
                >
                  Guardar Edición
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleEdit(borrador)}
                  className="px-4 py-2 text-sm text-on-surface-variant hover:text-primary-container border border-outline-variant/30 hover:border-primary/30 rounded-lg transition"
                >
                  Editar
                </button>
                <button
                  onClick={() => handleAprobar(borrador.id)}
                  disabled={approvingId === borrador.id}
                  className={`px-5 py-2 text-sm font-semibold rounded-lg transition-all ${
                    approvingId === borrador.id
                      ? "bg-white/10 text-on-surface-variant cursor-not-allowed"
                      : "bg-status-success text-on-primary hover:bg-status-success/90"
                  }`}
                >
                  {approvingId === borrador.id ? "Aprobando…" : "Aprobar y Programar"}
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
