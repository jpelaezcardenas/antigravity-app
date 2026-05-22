import type { ExAnteDetection } from "@/lib/types/contexia";

export function ExAnteDetectionCard({ data }: { data: ExAnteDetection }) {
  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 border-l-4 border-l-primary-container relative overflow-hidden shadow-[0_4px_24px_rgba(45,212,191,0.05)]">
      <div className="flex items-start gap-4">
        <div className="mt-1">
          <span className="material-symbols-outlined icon-fill text-primary-container">
            warning
          </span>
        </div>
        <div>
          <h3 className="font-title-md text-title-md text-primary-container mb-1">
            {data.title}
          </h3>
          <p className="font-body-md text-body-md text-on-surface-variant">
            {data.description}
          </p>
        </div>
      </div>
    </section>
  );
}
