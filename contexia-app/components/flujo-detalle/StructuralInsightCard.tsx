import { InsightCard } from "@/components/ui/InsightCard";
import type { StructuralFlowInsight } from "@/lib/types/contexia";

/**
 * Wrapper que delega a InsightCard con variant="accent"
 * Mantenido para compatibilidad con imports existentes.
 * @deprecated Use InsightCard directly with variant="accent"
 */
export function StructuralInsightCard({
  insight,
}: {
  insight: StructuralFlowInsight;
}) {
  return <InsightCard insight={insight} variant="accent" />;
}
