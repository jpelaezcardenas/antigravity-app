import type { StatusLevel } from "@/lib/types/contexia";
import { STATUS_COLOR, STATUS_BADGE } from "@/lib/styles/statusStyles";

/**
 * Badge genérico para mostrar estados de salud
 * Reemplaza mappings duplicados en múltiples componentes
 */
export function StatusBadge({ status }: { status: StatusLevel }) {
  return (
    <span className={`inline-block border rounded-full px-3 py-1 ${STATUS_COLOR[status]}`}>
      {STATUS_BADGE[status]}
    </span>
  );
}
