import type { TaxProvision } from "@/lib/types/contexia";
import { CARD_SHADOW } from "@/lib/styles/cardStyles";
import { formatCop } from "@/lib/format";
import {
  ProgressBar,
  VARIANT_TEXT_COLOR,
  variantFromGoal,
} from "@/components/ui/ProgressBar";

export function EstimatedTaxProvisionCard({
  provision,
}: {
  provision: TaxProvision;
}) {
  const variant = variantFromGoal(provision.goalPct);
  const reservedColor = VARIANT_TEXT_COLOR[variant];

  return (
    <section className={`bg-surface-elevated rounded-xl border border-white/10 p-5 flex flex-col gap-3 ${CARD_SHADOW.base} relative overflow-hidden`}>
      <div className="absolute -right-20 -top-20 w-40 h-40 bg-status-warning/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center gap-2">
        <span className="material-symbols-outlined text-status-warning text-[20px]">
          account_balance
        </span>
        <h3 className="font-body-md text-body-md text-primary-container">
          Provisión de IVA / Renta estimada
        </h3>
      </div>

      <div className="font-headline-xl text-headline-xl text-on-surface tracking-tight">
        {formatCop(provision.estimated)}
      </div>

      <div className="mt-2 flex flex-col gap-2">
        <div className="flex justify-between font-label-caps text-label-caps">
          <span className={reservedColor}>
            Reservado: {formatCop(provision.reserved)}
          </span>
          <span className="text-on-surface-variant">Meta</span>
        </div>
        <ProgressBar
          percent={provision.goalPct}
          variant={variant}
          trackClassName="bg-surface-container-highest"
        />
      </div>
    </section>
  );
}
