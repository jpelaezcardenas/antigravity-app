"use client";

import { useEffect, useState } from "react";
import {
  getB2bPaymentsGrid,
  createB2bClient,
  setB2bClientStatus,
  upsertB2bPayment,
  updateB2bClientContact,
  getB2bRetentionAlerts,
  PLAN_TIERS,
  type B2bPaymentsResponse,
  type B2bClient,
  type PlanTier,
  type RetentionAlert,
} from "@/lib/crm-api";

const PLAN_TIER_OPTION_LABEL: Record<PlanTier, string> = {
  freemium: "Freemium",
  starter: "Starter",
  growth: "Growth",
  enterprise: "Enterprise",
};
import { formatCop } from "@/lib/format";
import { HubspotSyncBadge } from "./HubspotSyncBadge";

const MONTH_LABELS: Record<string, string> = {
  "01": "Ene",
  "02": "Feb",
  "03": "Mar",
  "04": "Abr",
  "05": "May",
  "06": "Jun",
  "07": "Jul",
  "08": "Ago",
  "09": "Sep",
  "10": "Oct",
  "11": "Nov",
  "12": "Dic",
};

function periodLabel(period: string): string {
  const month = period.slice(5, 7);
  return MONTH_LABELS[month] ?? period;
}

const PROVISION_LABELS: Record<string, string> = {
  provisioned: "Login activo",
  pending_email: "Falta correo",
  not_provisioned: "Sin login",
};

export function B2bRetainersTab() {
  const [data, setData] = useState<B2bPaymentsResponse | null>(null);
  const [clientsById, setClientsById] = useState<Record<string, B2bClient>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const [showAltaForm, setShowAltaForm] = useState(false);
  const [altaName, setAltaName] = useState("");
  const [altaEmail, setAltaEmail] = useState("");
  const [altaPhone, setAltaPhone] = useState("");
  const [altaFeeCop, setAltaFeeCop] = useState("");
  const [altaPlanTier, setAltaPlanTier] = useState<PlanTier>("starter");
  const [inviteLink, setInviteLink] = useState<string | null>(null);

  const [editingCell, setEditingCell] = useState<{ clientId: string; period: string } | null>(null);
  const [editingValue, setEditingValue] = useState("");

  const [alerts, setAlerts] = useState<RetentionAlert[] | null>(null);
  const [alertsError, setAlertsError] = useState("");
  const [alertsLoading, setAlertsLoading] = useState(true);

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await getB2bPaymentsGrid();
      setData(res);
      const byId: Record<string, B2bClient> = {};
      res.grid.clients.forEach((c) => {
        byId[c.id] = c as B2bClient;
      });
      setClientsById(byId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar la grilla de pagos B2B");
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    setAlertsError("");
    setAlertsLoading(true);
    try {
      const res = await getB2bRetentionAlerts();
      setAlerts(res.items);
    } catch (e) {
      setAlertsError(e instanceof Error ? e.message : "No se pudieron cargar las alertas de retención");
    } finally {
      setAlertsLoading(false);
    }
  };

  useEffect(() => {
    load();
    loadAlerts();
  }, []);

  const handleAlta = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!altaName.trim()) return;
    setError("");
    setInviteLink(null);
    setBusyId("alta");
    try {
      const created = await createB2bClient({
        name: altaName.trim(),
        email: altaEmail.trim() || undefined,
        phone: altaPhone.trim() || undefined,
        monthly_fee_cents: altaFeeCop ? Math.round(Number(altaFeeCop) * 100) : undefined,
        plan_tier: altaPlanTier,
      });
      setAltaName("");
      setAltaEmail("");
      setAltaPhone("");
      setAltaFeeCop("");
      setAltaPlanTier("starter");
      if (created.invite_link) {
        setInviteLink(created.invite_link);
      } else {
        setShowAltaForm(false);
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo crear el cliente");
    } finally {
      setBusyId(null);
    }
  };

  const toggleStatus = async (client: B2bClient) => {
    const nextStatus = client.status === "activo" ? "inactivo" : "activo";
    setError("");
    setBusyId(client.id);
    try {
      await setB2bClientStatus(client.id, nextStatus);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cambiar el estado del cliente");
    } finally {
      setBusyId(null);
    }
  };

  const startEditingCell = (clientId: string, period: string, currentCents: number) => {
    setEditingCell({ clientId, period });
    setEditingValue(currentCents > 0 ? String(currentCents / 100) : "");
  };

  const commitCellEdit = async () => {
    if (!editingCell) return;
    const { clientId, period } = editingCell;
    const amountCents = editingValue.trim() ? Math.round(Number(editingValue) * 100) : 0;
    setEditingCell(null);
    if (Number.isNaN(amountCents)) return;
    setError("");
    setBusyId(clientId);
    try {
      await upsertB2bPayment(clientId, period, amountCents);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo registrar el pago");
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
        Cargando clientes B2B…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-4 text-status-critical text-sm">
        {error || "No se pudo cargar la grilla de pagos B2B"}
      </div>
    );
  }

  const { grid, totals, source } = data;

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-3 text-status-critical text-sm">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant">
            Retenedores B2B
          </p>
          <p className="text-sm text-on-surface-variant">
            Fuente: <span className="text-on-surface">{source}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              setShowAltaForm((v) => !v);
              setInviteLink(null);
            }}
            className="rounded-xl border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary-container hover:bg-primary/20"
          >
            {showAltaForm ? "Cancelar" : "+ Nuevo cliente"}
          </button>
          <div className="rounded-xl border border-primary/20 bg-primary/10 px-4 py-2 text-right">
            <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">
              Total del periodo
            </p>
            <p className="font-headline-sm text-headline-sm text-primary-container font-bold">
              {formatCop(totals.grand_total / 100)}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-outline-variant/20 bg-white/5 p-4">
        <p className="mb-3 text-xs uppercase tracking-[0.2em] text-on-surface-variant">
          Alertas de retención
        </p>
        {alertsLoading ? (
          <p className="text-sm text-on-surface-variant">Evaluando riesgo de retención…</p>
        ) : alertsError ? (
          <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-3 text-status-critical text-sm">
            {alertsError}
          </div>
        ) : !alerts || alerts.length === 0 ? (
          <p className="text-sm text-on-surface-variant">
            Sin alertas de retención por ahora.
          </p>
        ) : (
          <ul className="space-y-2">
            {alerts.map((alert, index) => (
              <li
                key={`${alert.id}-${index}`}
                className="flex items-center justify-between gap-3 rounded-xl border border-status-warning/30 bg-status-warning/10 px-3 py-2 text-sm"
              >
                <span className="text-on-surface">
                  {clientsById[alert.client_id]?.name ?? alert.client_id}
                </span>
                <span className="text-xs text-status-warning">{alert.message}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {showAltaForm && (
        <form
          onSubmit={handleAlta}
          className="grid grid-cols-1 gap-3 rounded-2xl border border-outline-variant/20 bg-white/5 p-4 sm:grid-cols-4"
        >
          <input
            required
            placeholder="Nombre del cliente"
            value={altaName}
            onChange={(e) => setAltaName(e.target.value)}
            className="rounded-lg border border-outline-variant/30 bg-transparent px-3 py-2 text-sm text-on-surface"
          />
          <input
            type="email"
            placeholder="Correo (opcional — sin correo no hay login)"
            value={altaEmail}
            onChange={(e) => setAltaEmail(e.target.value)}
            className="rounded-lg border border-outline-variant/30 bg-transparent px-3 py-2 text-sm text-on-surface"
          />
          <input
            placeholder="Teléfono"
            value={altaPhone}
            onChange={(e) => setAltaPhone(e.target.value)}
            className="rounded-lg border border-outline-variant/30 bg-transparent px-3 py-2 text-sm text-on-surface"
          />
          <input
            type="number"
            min="0"
            placeholder="Retainer mensual (COP)"
            value={altaFeeCop}
            onChange={(e) => setAltaFeeCop(e.target.value)}
            className="rounded-lg border border-outline-variant/30 bg-transparent px-3 py-2 text-sm text-on-surface"
          />
          <select
            value={altaPlanTier}
            onChange={(e) => setAltaPlanTier(e.target.value as PlanTier)}
            className="rounded-lg border border-outline-variant/30 bg-transparent px-3 py-2 text-sm text-on-surface"
          >
            {PLAN_TIERS.map((tier) => (
              <option key={tier} value={tier} className="bg-surface-container text-on-surface">
                {PLAN_TIER_OPTION_LABEL[tier]}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={busyId === "alta"}
            className="sm:col-span-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-on-primary disabled:opacity-50"
          >
            {busyId === "alta" ? "Creando…" : "Crear cliente"}
          </button>
          {inviteLink && (
            <div className="sm:col-span-4 rounded-lg border border-primary/30 bg-primary/10 p-3 text-sm text-on-surface">
              <p className="mb-1 font-semibold text-primary-container">
                Cliente creado. Copia y envía este link de acceso:
              </p>
              <div className="flex items-center gap-2">
                <input
                  readOnly
                  value={inviteLink}
                  onFocus={(e) => e.currentTarget.select()}
                  className="flex-1 rounded-lg border border-outline-variant/30 bg-transparent px-3 py-2 text-xs text-on-surface-variant"
                />
                <button
                  type="button"
                  onClick={() => navigator.clipboard?.writeText(inviteLink)}
                  className="rounded-lg border border-primary/30 px-3 py-2 text-xs font-semibold text-primary-container hover:bg-primary/20"
                >
                  Copiar
                </button>
              </div>
            </div>
          )}
        </form>
      )}

      {grid.clients.length === 0 ? (
        <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
          Sin clientes B2B registrados todavía.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-outline-variant/20 bg-white/5">
          <table className="w-full min-w-[820px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-outline-variant/30 text-left text-on-surface-variant">
                <th className="px-4 py-3 font-semibold">Cliente</th>
                <th className="px-4 py-3 font-semibold">Contacto</th>
                <th className="px-4 py-3 font-semibold">Login</th>
                <th className="px-4 py-3 font-semibold">Estado</th>
                <th className="px-4 py-3 font-semibold">HubSpot</th>
                {grid.periods.map((period) => (
                  <th key={period} className="px-4 py-3 text-right font-semibold">
                    {periodLabel(period)}
                  </th>
                ))}
                <th className="px-4 py-3 text-right font-semibold">Total</th>
              </tr>
            </thead>
            <tbody>
              {grid.clients.map((client) => {
                const full = clientsById[client.id];
                return (
                  <tr key={client.id} className="border-b border-outline-variant/10 last:border-0">
                    <td className="px-4 py-3 text-on-surface font-medium">{client.name}</td>
                    <td className="px-4 py-3 text-xs text-on-surface-variant">
                      {full?.email || "—"}
                      {full?.phone ? ` · ${full.phone}` : ""}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      <span
                        className={
                          full?.provision_status === "provisioned"
                            ? "text-status-success"
                            : "text-on-surface-variant/70"
                        }
                      >
                        {PROVISION_LABELS[full?.provision_status ?? "not_provisioned"]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        disabled={busyId === client.id}
                        onClick={() => toggleStatus({ ...client, status: client.status } as B2bClient)}
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase disabled:opacity-50 ${
                          client.status === "activo"
                            ? "bg-status-success/10 text-status-success"
                            : "bg-outline-variant/20 text-on-surface-variant"
                        }`}
                        title={client.status === "activo" ? "Dar de baja" : "Reactivar"}
                      >
                        {client.status}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <HubspotSyncBadge
                        objectType="company"
                        hubspotId={full?.hubspot_company_id}
                        lastSyncedAt={full?.last_synced_at}
                      />
                    </td>
                    {grid.periods.map((period) => {
                      const amount = grid.cells[client.id]?.[period] ?? 0;
                      const isEditing =
                        editingCell?.clientId === client.id && editingCell.period === period;
                      return (
                        <td
                          key={period}
                          className={`px-4 py-3 text-right ${
                            amount > 0 ? "text-on-surface" : "text-on-surface-variant/50"
                          }`}
                        >
                          {isEditing ? (
                            <input
                              autoFocus
                              type="number"
                              min="0"
                              value={editingValue}
                              onChange={(e) => setEditingValue(e.target.value)}
                              onBlur={commitCellEdit}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") commitCellEdit();
                                if (e.key === "Escape") setEditingCell(null);
                              }}
                              className="w-24 rounded border border-primary/40 bg-transparent px-1 py-0.5 text-right text-xs text-on-surface"
                            />
                          ) : (
                            <button
                              type="button"
                              onClick={() => startEditingCell(client.id, period, amount)}
                              className="hover:underline"
                              title="Click para registrar/editar el pago"
                            >
                              {amount > 0 ? formatCop(amount / 100) : "—"}
                            </button>
                          )}
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-right font-bold text-primary-container">
                      {formatCop((totals.by_client[client.id] ?? 0) / 100)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t border-outline-variant/30 bg-white/5">
                <td className="px-4 py-3 font-bold text-on-surface" colSpan={4}>
                  Total
                </td>
                {grid.periods.map((period) => (
                  <td key={period} className="px-4 py-3 text-right font-bold text-on-surface">
                    {formatCop((totals.by_period[period] ?? 0) / 100)}
                  </td>
                ))}
                <td className="px-4 py-3 text-right font-bold text-primary-container">
                  {formatCop(totals.grand_total / 100)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
