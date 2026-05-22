"use client";

import { useState } from "react";
import type { WithdrawalScenario } from "@/lib/types/contexia";
import { calculateWithdrawalImpact } from "@/lib/utils/calculations";
import { formatCop } from "@/lib/format";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CARD_SHADOW } from "@/lib/styles/cardStyles";

export function WithdrawalSimulatorCard({
  initialWithdrawal,
  cashWithoutWithdrawal,
}: {
  initialWithdrawal: WithdrawalScenario;
  cashWithoutWithdrawal: number;
}) {
  const [amount, setAmount] = useState(initialWithdrawal.amount);
  const impact = calculateWithdrawalImpact(amount, cashWithoutWithdrawal);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value === "" ? 0 : Math.max(0, parseInt(e.target.value) || 0);
    setAmount(val);
  };

  const formattedAmount =
    amount === 0 ? "" : (amount / 1000000).toFixed(1);

  return (
    <section className={`bg-surface-elevated rounded-xl border border-white/10 p-5 flex flex-col gap-4 ${CARD_SHADOW.base}`}>
      <div>
        <h3 className="font-title-md text-title-md text-primary-container">
          Simulador de Retiro
        </h3>
        <p className="font-body-md text-body-md text-on-surface-variant mt-1">
          Proyecta el impacto en caja según monto a retirar
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="withdrawal-input" className="font-label-caps text-label-caps text-on-surface">
          Monto a Retirar (en millones)
        </label>
        <div className="relative">
          <input
            id="withdrawal-input"
            type="number"
            step="0.1"
            min="0"
            value={formattedAmount}
            onChange={handleInputChange}
            placeholder="0.0"
            className="w-full bg-surface-container border border-outline-variant/30 rounded-lg px-4 py-3 font-data-mono text-data-mono text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50"
          />
          <span className="absolute right-4 top-3 font-label-caps text-label-caps text-on-surface-variant pointer-events-none">
            MM $
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-surface-container rounded-lg p-4 border border-white/5">
          <p className="font-label-caps text-label-caps text-on-surface-variant">
            Caja Sin Retiro
          </p>
          <div className="font-data-mono text-data-mono text-on-surface mt-2 font-bold">
            {formatCop(cashWithoutWithdrawal)}
          </div>
        </div>

        <div className="bg-surface-container rounded-lg p-4 border border-white/5">
          <p className="font-label-caps text-label-caps text-on-surface-variant">
            Caja Con Retiro
          </p>
          <div className="font-data-mono text-data-mono text-primary mt-2 font-bold">
            {formatCop(impact.cashWithWithdrawal)}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <StatusBadge status={impact.status} />
      </div>

      <p className="font-body-md text-body-md text-on-surface-variant pt-2 border-t border-white/5">
        {impact.message}
      </p>
    </section>
  );
}
