"use client";

import { useEffect, useState } from "react";
import {
  generateHooks,
  evaluateHooks,
  createCampaignPackage,
  listCampaigns,
  approveCampaignPackage,
  rejectCampaignPackage,
  type Hook,
  type CampaignPackage,
} from "@/lib/sell-machine-api";

export function SellMachineSection() {
  const [hooks, setHooks] = useState<Hook[]>([]);
  const [survivors, setSurvivors] = useState<Hook[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignPackage[]>([]);
  const [brief, setBrief] = useState("");
  const [targetSegment, setTargetSegment] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadCampaigns = async () => {
    setError("");
    setLoading(true);
    try {
      const result = await listCampaigns("pending_approval");
      setCampaigns(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar los campaign packages");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  const handleGenerate = async () => {
    setError("");
    setBusy(true);
    try {
      const result = await generateHooks(5);
      setHooks(result.hooks);
      setSurvivors([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron generar hooks");
    } finally {
      setBusy(false);
    }
  };

  const handleEvaluate = async () => {
    setError("");
    setBusy(true);
    try {
      const result = await evaluateHooks(hooks);
      setSurvivors(result.survivors);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo evaluar los hooks");
    } finally {
      setBusy(false);
    }
  };

  const handleCreatePackage = async () => {
    setError("");
    setBusy(true);
    try {
      await createCampaignPackage({
        hooks: survivors,
        brief,
        target_segment: targetSegment,
        budget: null,
      });
      setHooks([]);
      setSurvivors([]);
      setBrief("");
      setTargetSegment("");
      await loadCampaigns();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo crear el campaign package");
    } finally {
      setBusy(false);
    }
  };

  const handleApprove = async (campaign: CampaignPackage) => {
    setError("");
    setBusy(true);
    try {
      await approveCampaignPackage(campaign.id, "admin@contexia.online");
      await loadCampaigns();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo aprobar el campaign package");
    } finally {
      setBusy(false);
    }
  };

  const handleReject = async (campaign: CampaignPackage) => {
    setError("");
    setBusy(true);
    try {
      await rejectCampaignPackage(campaign.id, "Rechazado desde el Bunker", "admin@contexia.online");
      await loadCampaigns();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo rechazar el campaign package");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <section className="mb-2">
        <h2 className="font-headline-lg text-headline-lg text-primary-container mb-2">
          Sell Machine
        </h2>
        <p className="text-on-surface-variant text-body-md">
          Copywriter → Content Critic → Approval Queue: genera hooks, filtra los que no cumplen la
          marca, y aprueba el campaign package final.
        </p>
      </section>

      {error && (
        <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-4 text-status-critical text-sm">
          {error}
        </div>
      )}

      <div className="rounded-2xl border border-outline-variant/20 bg-white/5 p-4 space-y-4">
        <div className="flex gap-3">
          <button
            type="button"
            disabled={busy}
            onClick={handleGenerate}
            className="rounded-lg bg-primary text-on-primary px-4 py-2 text-sm font-bold hover:bg-primary-fixed-dim disabled:opacity-50"
          >
            Generar Hooks
          </button>
          {hooks.length > 0 && (
            <button
              type="button"
              disabled={busy}
              onClick={handleEvaluate}
              className="rounded-lg border border-status-warning/40 bg-status-warning/10 px-4 py-2 text-sm font-semibold text-status-warning hover:bg-status-warning/15 disabled:opacity-50"
            >
              Evaluar
            </button>
          )}
        </div>

        {hooks.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant mb-2">
              Hooks generados ({hooks.length})
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {hooks.map((hook, i) => (
                <div key={i} className="rounded-xl border border-outline-variant/30 bg-surface-elevated p-3">
                  <p className="text-sm font-semibold text-on-surface">{hook.headline}</p>
                  <p className="mt-1 text-xs text-on-surface-variant">{hook.body}</p>
                  <p className="mt-1 text-xs text-primary-container">{hook.cta}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {survivors.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.2em] text-status-success">
              Sobrevivientes ({survivors.length})
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {survivors.map((hook, i) => (
                <div key={i} className="rounded-xl border border-status-success/40 bg-status-success/10 p-3">
                  <p className="text-sm font-semibold text-on-surface">{hook.headline}</p>
                  <p className="mt-1 text-xs text-on-surface-variant">{hook.body}</p>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Creative brief"
                value={brief}
                onChange={(e) => setBrief(e.target.value)}
                className="rounded-lg border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface"
              />
              <input
                type="text"
                placeholder="Target segment"
                value={targetSegment}
                onChange={(e) => setTargetSegment(e.target.value)}
                className="rounded-lg border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface"
              />
            </div>
            <button
              type="button"
              disabled={busy || !brief || !targetSegment}
              onClick={handleCreatePackage}
              className="rounded-lg bg-primary text-on-primary px-4 py-2 text-sm font-bold hover:bg-primary-fixed-dim disabled:opacity-50"
            >
              Crear Campaign Package
            </button>
          </div>
        )}
      </div>

      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant mb-2">
          Campaign Packages Pendientes
        </p>
        {loading ? (
          <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
            Cargando…
          </div>
        ) : campaigns.length === 0 ? (
          <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
            Sin campaign packages pendientes.
          </div>
        ) : (
          <div className="space-y-3">
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="rounded-xl border border-outline-variant/30 bg-surface-elevated p-4">
                <p className="text-sm font-semibold text-on-surface">{campaign.payload.creative_brief}</p>
                <p className="mt-1 text-xs text-on-surface-variant">
                  Segmento: {campaign.payload.target_segment} · {campaign.payload.hooks.length} hooks
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => handleApprove(campaign)}
                    className="rounded-lg bg-primary text-on-primary py-2 text-xs font-bold hover:bg-primary-fixed-dim disabled:opacity-50"
                  >
                    Aprobar
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => handleReject(campaign)}
                    className="rounded-lg border border-status-critical/40 bg-status-critical/10 py-2 text-xs font-semibold text-status-critical hover:bg-status-critical/15 disabled:opacity-50"
                  >
                    Rechazar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
