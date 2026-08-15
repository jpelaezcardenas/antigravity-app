"use client";

import { useEffect, useMemo, useState } from "react";
import {
  getB2cPipeline,
  advanceCrmLead,
  approveCrmPayment,
  type CrmLead,
  type CrmStage,
} from "@/lib/crm-api";
import { HubspotSyncBadge } from "./HubspotSyncBadge";

const COLUMNS: { id: CrmStage; label: string }[] = [
  { id: "NUEVOS", label: "Nuevos" },
  { id: "PROSPECTOS", label: "Prospectos" },
  { id: "POR_APROBAR", label: "Por Aprobar" },
  { id: "LISTOS_CONTADORA", label: "Listos Contadora" },
];

const NEXT_STAGE: Partial<Record<CrmStage, CrmStage>> = {
  NUEVOS: "PROSPECTOS",
  PROSPECTOS: "POR_APROBAR",
};

export function B2cKanbanTab() {
  const [leads, setLeads] = useState<CrmLead[]>([]);
  const [source, setSource] = useState<"supabase" | "demo_fallback">("demo_fallback");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await getB2cPipeline();
      setLeads(res.columns.flatMap((col) => col.leads));
      setSource(res.source);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar el embudo B2C");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<CrmStage, CrmLead[]>();
    COLUMNS.forEach((col) => map.set(col.id, []));
    leads.forEach((lead) => map.get(lead.stage)?.push(lead));
    return map;
  }, [leads]);

  const advance = async (lead: CrmLead) => {
    const nextStage = NEXT_STAGE[lead.stage];
    if (!nextStage) return;
    setError("");
    setBusyId(lead.id);
    try {
      await advanceCrmLead(lead.id, nextStage);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo avanzar el lead");
    } finally {
      setBusyId(null);
    }
  };

  const approvePayment = async (lead: CrmLead) => {
    setError("");
    setBusyId(lead.id);
    try {
      await approveCrmPayment(lead.id, "admin@contexia.online");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo aprobar el pago");
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
        Cargando embudo B2C…
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
          <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant">
            Renta Natural 2026
          </p>
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
              {(grouped.get(col.id) || []).map((lead) => (
                <div key={lead.id} className="rounded-xl border border-outline-variant/30 bg-surface-elevated p-3">
                  <p className="text-sm text-on-surface leading-snug font-medium">{lead.full_name}</p>
                  {lead.last_message && (
                    <p className="mt-1 text-xs text-on-surface-variant line-clamp-2">{lead.last_message}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-on-surface-variant">
                    <span className="rounded-md border border-outline-variant/30 bg-white/5 px-2 py-0.5">
                      {lead.score}/100
                    </span>
                    <HubspotSyncBadge
                      objectType="deal"
                      hubspotId={lead.hubspot_deal_id}
                      lastSyncedAt={lead.last_synced_at}
                    />
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-2">
                    {lead.stage === "POR_APROBAR" && (
                      <button
                        disabled={busyId === lead.id}
                        onClick={() => approvePayment(lead)}
                        className="rounded-lg bg-primary text-on-primary py-2 text-xs font-bold hover:bg-primary-fixed-dim disabled:opacity-50"
                      >
                        Aprobar Pago
                      </button>
                    )}
                    {NEXT_STAGE[lead.stage] && (
                      <button
                        disabled={busyId === lead.id}
                        onClick={() => advance(lead)}
                        className="rounded-lg border border-status-warning/40 bg-status-warning/10 py-2 text-xs font-semibold text-status-warning hover:bg-status-warning/15 disabled:opacity-50"
                      >
                        Avanzar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
