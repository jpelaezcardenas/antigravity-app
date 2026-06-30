import type { PatrimonioTotal } from "@/lib/types/contexia";
import { formatCop } from "@/lib/format";

export function TotalEquityCard({
  patrimonio,
}: {
  patrimonio: PatrimonioTotal;
}) {
  return (
    <section className="relative p-[1px] rounded-xl bg-gradient-to-br from-primary/40 via-surface-elevated to-primary/20 shadow-[0_0_40px_rgba(45,212,191,0.2)]">
      <div className="bg-surface-elevated/95 backdrop-blur-md rounded-xl p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-primary-container">
              Patrimonio Total
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant mt-1">
              Composición del capital
            </p>
          </div>
          <div className="absolute -right-12 -top-12 w-32 h-32 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
        </div>

        <div className="pt-4">
          <div className="font-headline-xl text-headline-xl text-primary tracking-tight">
            {formatCop(patrimonio.total)}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
          <div className="bg-surface-container rounded-lg p-4 border border-white/5">
            <p className="font-label-caps text-label-caps text-on-surface-variant">
              Utilidades Retenidas
            </p>
            <div className="font-data-mono text-data-mono text-on-surface mt-2 font-bold">
              {formatCop(patrimonio.retainedEarnings)}
            </div>
            <p className="font-body-xs text-body-xs text-on-surface-variant mt-1">
              {Math.round((patrimonio.retainedEarnings / patrimonio.total) * 100)}%
              del total
            </p>
          </div>

          <div className="bg-surface-container rounded-lg p-4 border border-white/5">
            <p className="font-label-caps text-label-caps text-on-surface-variant">
              Utilidad Ejercicio
            </p>
            <div className="font-data-mono text-data-mono text-primary mt-2 font-bold">
              {formatCop(patrimonio.currentYearEarnings)}
            </div>
            <p className="font-body-xs text-body-xs text-on-surface-variant mt-1">
              {Math.round((patrimonio.currentYearEarnings / patrimonio.total) * 100)}%
              del total
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
