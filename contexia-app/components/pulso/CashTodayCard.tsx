import Link from "next/link";
import type { CashToday } from "@/lib/types/contexia";
import { formatCop } from "@/lib/format";

export function CashTodayCard({ cash }: { cash: CashToday }) {
  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] relative overflow-hidden">
      <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-status-success/10 to-transparent pointer-events-none" />

      <div className="relative z-10">
        <h2 className="font-body-md text-body-md text-primary-container mb-2">
          Caja Real de Hoy
        </h2>
        <div className="font-headline-xl text-headline-xl text-status-success mb-1 tracking-tight">
          {formatCop(cash.total)}
        </div>
        <p className="font-body-md text-body-md text-on-surface mb-6">
          Sabe cuánto es tuyo: {formatCop(cash.yours)}
        </p>

        <div className="flex flex-col gap-2 border-t border-outline-variant/30 pt-4">
          <div className="flex justify-between items-center">
            <span className="font-data-mono text-data-mono text-on-surface-variant">
              Ventas de ayer:
            </span>
            <span className="font-data-mono text-data-mono text-on-surface">
              {formatCop(cash.yesterdaySales)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-data-mono text-data-mono text-on-surface-variant">
              Gastos:
            </span>
            <span className="font-data-mono text-data-mono text-on-surface">
              {formatCop(cash.expenses)}
            </span>
          </div>
        </div>

        {cash.detailHref && (
          <Link
            href={cash.detailHref}
            className="mt-6 w-full flex items-center justify-center gap-2 py-2 border border-primary-container/20 rounded-lg text-primary-container hover:bg-primary-container/10 transition-all active:scale-[0.98]"
          >
            <span className="font-label-caps text-label-caps">
              Ver desglose estructural
            </span>
            <span className="material-symbols-outlined text-sm">
              chevron_right
            </span>
          </Link>
        )}
      </div>
    </section>
  );
}
