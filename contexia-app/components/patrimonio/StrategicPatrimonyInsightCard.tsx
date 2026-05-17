import { InsightCard } from "@/components/ui/InsightCard";
import type { StrategicPatrimonioInsight } from "@/lib/types/contexia";

/**
 * Wrapper que delega a InsightCard con variant="gradient"
 * Mantenido para compatibilidad con imports existentes.
 * @deprecated Use InsightCard directly with variant="gradient" showLabel=true
 */
export function StrategicPatrimonyInsightCard({
  insight,
}: {
  insight: StrategicPatrimonioInsight;
}) {
  return <InsightCard insight={insight} variant="gradient" showLabel={true} />;
}
