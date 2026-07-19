"use client";

import { useEffect, useState } from "react";
import { getB2bPaymentsGrid, type B2bPaymentsResponse } from "@/lib/crm-api";
import { formatCop } from "@/lib/format";

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

export function B2bRetainersTab() {
  const [data, setData] = useState<B2bPaymentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await getB2bPaymentsGrid();
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar la grilla de pagos B2B");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
        Cargando clientes B2B…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-status-critical/40 bg-status-critical/10 p-4 text-status-critical text-sm">
        {error}
      </div>
    );
  }

  if (!data || data.grid.clients.length === 0) {
    return (
      <div className="rounded-xl border border-outline-variant/30 bg-surface-container p-6 text-on-surface-variant">
        Sin clientes B2B registrados todavía.
      </div>
    );
  }

  const { grid, totals, source } = data;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-on-surface-variant">
            Retenedores B2B
          </p>
          <p className="text-sm text-on-surface-variant">
            Fuente: <span className="text-on-surface">{source}</span>
          </p>
        </div>
        <div className="rounded-xl border border-primary/20 bg-primary/10 px-4 py-2 text-right">
          <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">
            Total del periodo
          </p>
          <p className="font-headline-sm text-headline-sm text-primary-container font-bold">
            {formatCop(totals.grand_total / 100)}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-outline-variant/20 bg-white/5">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-outline-variant/30 text-left text-on-surface-variant">
              <th className="px-4 py-3 font-semibold">Cliente</th>
              <th className="px-4 py-3 font-semibold">Estado</th>
              {grid.periods.map((period) => (
                <th key={period} className="px-4 py-3 text-right font-semibold">
                  {periodLabel(period)}
                </th>
              ))}
              <th className="px-4 py-3 text-right font-semibold">Total</th>
            </tr>
          </thead>
          <tbody>
            {grid.clients.map((client) => (
              <tr key={client.id} className="border-b border-outline-variant/10 last:border-0">
                <td className="px-4 py-3 text-on-surface font-medium">{client.name}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                      client.status === "activo"
                        ? "bg-status-success/10 text-status-success"
                        : "bg-outline-variant/20 text-on-surface-variant"
                    }`}
                  >
                    {client.status}
                  </span>
                </td>
                {grid.periods.map((period) => {
                  const amount = grid.cells[client.id]?.[period] ?? 0;
                  return (
                    <td
                      key={period}
                      className={`px-4 py-3 text-right ${
                        amount > 0 ? "text-on-surface" : "text-on-surface-variant/50"
                      }`}
                    >
                      {amount > 0 ? formatCop(amount / 100) : "—"}
                    </td>
                  );
                })}
                <td className="px-4 py-3 text-right font-bold text-primary-container">
                  {formatCop((totals.by_client[client.id] ?? 0) / 100)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-outline-variant/30 bg-white/5">
              <td className="px-4 py-3 font-bold text-on-surface" colSpan={2}>
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
    </div>
  );
}
