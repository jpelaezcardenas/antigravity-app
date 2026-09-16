import { InsightCard } from "@/components/ui/InsightCard";
import type { StrategicPatrimonioInsight } from "@/lib/types/contexia";

/**
 * Wrapper que delega a InsightCard (estilo único desde 2026-09-16 — ver ese archivo).
 * Mantenido para compatibilidad con imports existentes.
 * @deprecated Use InsightCard directly with showLabel=true
 */
export function StrategicPatrimonyInsightCard({
  insight,
}: {
  insight: StrategicPatrimonioInsight;
}) {
  return <InsightCard insight={insight} showLabel={true} />;
}
