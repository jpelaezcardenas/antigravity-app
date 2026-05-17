import type { EquityMovement } from "@/lib/types/contexia";
import { formatCop } from "@/lib/format";
import { DIRECTION_ICON, DIRECTION_COLOR } from "@/lib/styles/statusStyles";

export function EquityMovementHistoryCard({
  movements,
}: {
  movements: EquityMovement[];
}) {
  return (
    <section className="flex flex-col gap-4">
      <h3 className="font-title-md text-title-md text-primary-container border-b border-white/5 pb-2">
        Historial de Movimientos
      </h3>
      <div className="flex flex-col gap-3">
        {movements.map((m) => {
          const dirInfo = DIRECTION_ICON[m.direction];
          return (
            <div
              key={m.id}
              className="bg-surface-container border border-outline-variant/20 rounded-lg p-4 flex items-center gap-4 hover:border-primary/30 transition-colors"
            >
              <div className="flex flex-col items-center justify-center bg-surface w-12 h-12 rounded border border-white/5 shrink-0">
                <span className={`material-symbols-outlined ${dirInfo.color}`}>
                  {dirInfo.icon}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-body-md text-body-md font-semibold text-on-surface truncate">
                  {m.label}
                </h4>
                <p className="font-label-caps text-label-caps text-on-surface-variant truncate">
                  {m.date}
                </p>
              </div>
              <div
                className={`font-data-mono text-data-mono text-right shrink-0 font-bold ${DIRECTION_COLOR[m.direction]}`}
              >
                {m.amount > 0 ? "+" : ""}
                {formatCop(m.amount)}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
