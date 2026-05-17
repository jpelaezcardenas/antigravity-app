import Link from "next/link";

export function StructuralBreakdownCTA() {
  return (
    <Link href="/flujo-detalle">
      <div className="bg-gradient-to-br from-primary/20 to-ai-narrative-tint/10 border border-primary/30 rounded-xl p-5 flex items-center justify-between hover:border-primary/50 transition-all hover:shadow-[0_0_20px_rgba(45,212,191,0.15)] cursor-pointer group">
        <div className="flex flex-col gap-1">
          <h3 className="font-title-md text-title-md text-primary-container">
            Ver desglose estructural
          </h3>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Análisis detallado de flujos y salud financiera
          </p>
        </div>
        <span className="material-symbols-outlined text-primary group-hover:translate-x-1 transition-transform">
          arrow_forward
        </span>
      </div>
    </Link>
  );
}
