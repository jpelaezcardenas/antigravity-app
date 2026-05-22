import type { ShadowAuditMatch } from "@/lib/types/contexia";

export function ShadowAuditCard({ data }: { data: ShadowAuditMatch }) {
  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-ai-narrative-tint/10 to-transparent opacity-50 pointer-events-none" />

      <div className="relative z-10 flex flex-col gap-4">
        <div className="flex items-center gap-3 border-b border-outline-variant/30 pb-3">
          <span className="material-symbols-outlined text-primary-container">
            policy
          </span>
          <h3 className="font-title-md text-title-md text-primary-container">
            {data.title}
          </h3>
        </div>
        <div className="flex items-start gap-4">
          <span className="material-symbols-outlined text-primary-container mt-1">
            check_circle
          </span>
          <p className="font-body-md text-body-md text-inverse-surface">
            <strong className="text-on-surface font-semibold">
              {data.highlight}
            </strong>{" "}
            {data.description}
          </p>
        </div>
      </div>
    </section>
  );
}
