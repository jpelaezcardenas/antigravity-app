import type { Insight } from "@/lib/types/contexia";

/**
 * Tarjeta de insight genérica para Radar, Patrimonio y FlujoDetalle.
 * Reemplaza: StrategicInsightCard, StrategicPatrimonyInsightCard, StructuralFlowInsightCard.
 *
 * 2026-09-16 (founder request): unificado a un solo estilo — el de
 * `components/pulso/NoteOfDayCard.tsx` ("Hoy en tu negocio") — en vez de las tres variantes
 * divergentes ("elevated"/"accent"/"gradient") que este componente tenía antes. Eran tres
 * tratamientos visuales genuinamente distintos para el mismo rol de UI (una nota con voz de
 * IA), la causa real de que la app se sintiera con "demasiados estilos distintos".
 */
export function InsightCard({
  insight,
  showLabel = false,
  label = "Insight Estratégico",
}: {
  insight: Insight;
  showLabel?: boolean;
  label?: string;
}) {
  return (
    <section className="relative bg-surface-elevated/50 backdrop-blur-md rounded-xl p-6 border border-ai-narrative-tint/30 shadow-[0_0_30px_rgba(139,92,246,0.1)]">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-ai-narrative-tint/20 flex items-center justify-center shrink-0 border border-ai-narrative-tint/50">
          <span className="material-symbols-outlined icon-fill text-secondary-fixed-dim">
            auto_awesome
          </span>
        </div>
        <div>
          {showLabel && (
            <h2 className="font-title-md text-title-md text-primary-container mb-1">
              {label}
            </h2>
          )}
          <p className="font-body-lg text-body-lg text-on-surface leading-relaxed">
            {insight.body.map((seg, i) =>
              seg.highlight ? (
                <span key={i} className="text-primary font-semibold">
                  {seg.text}
                </span>
              ) : (
                <span key={i}>{seg.text}</span>
              ),
            )}
          </p>
        </div>
      </div>
    </section>
  );
}
