import type { DividendShield } from "@/lib/types/contexia";
import { CARD_SHADOW } from "@/lib/styles/cardStyles";
import { formatCop } from "@/lib/format";

export function DividendShieldCard({
  shield,
}: {
  shield: DividendShield;
}) {
  return (
    <section className={`bg-surface-elevated rounded-xl border border-status-success/20 p-5 flex flex-col gap-3 ${CARD_SHADOW.base} relative overflow-hidden`}>
      <div className="absolute -right-12 -top-12 w-40 h-40 bg-status-success/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center gap-2">
        <span className="material-symbols-outlined text-status-success text-[20px]">
          security
        </span>
        <h3 className="font-body-md text-body-md text-primary-container">
          Escudo de Dividendos
        </h3>
      </div>

      <div className="flex items-end gap-4">
        <div>
          <p className="font-label-caps text-label-caps text-on-surface-variant mb-2">
            Retiro Seguro Máximo
          </p>
          <div className="font-headline-xl text-headline-xl text-on-surface tracking-tight">
            {formatCop(shield.safeAmount)}
          </div>
        </div>
        <div className="ml-auto">
          <div className="inline-block bg-status-success/10 border border-status-success/30 rounded-full px-3 py-1">
            <span className="font-label-caps text-label-caps text-status-success font-bold">
              {shield.safeZoneLabel}
            </span>
          </div>
        </div>
      </div>

      <p className="font-body-sm text-body-sm text-on-surface-variant pt-2 border-t border-white/5">
        {shield.riskLabel}
      </p>
    </section>
  );
}
