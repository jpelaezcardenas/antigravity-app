import { InsightCard } from "@/components/ui/InsightCard";
import type { StructuralFlowInsight } from "@/lib/types/contexia";

/**
 * Wrapper que delega a InsightCard (estilo único desde 2026-09-16 — ver ese archivo).
 * Mantenido para compatibilidad con imports existentes.
 * @deprecated Use InsightCard directly
 */
export function StructuralInsightCard({
  insight,
}: {
  insight: StructuralFlowInsight;
}) {
  return <InsightCard insight={insight} />;
}
