/**
 * PWA V2 pilot (Fase 4) — same static brand copy as /app/acerca (verbatim,
 * nothing invented), with the Weather-style hero treatment applied directly
 * in code (no separate Stitch round for this secondary/detail screen — low
 * risk, content-only page, same visual language already approved).
 */
const PILLARS: { icon: string; title: string; description: string }[] = [
  {
    icon: "monitoring",
    title: "Pulso Diario",
    description: "Cuánta plata real tienes hoy, sin adivinar.",
  },
  {
    icon: "shield",
    title: "Centinela Fiscal",
    description: "Te avisa antes de que la DIAN te avise a ti.",
  },
  {
    icon: "insights",
    title: "Radar Predictivo",
    description: "Hacia dónde va tu caja las próximas semanas.",
  },
  {
    icon: "fact_check",
    title: "Auditoría Sombra",
    description: "Revisa tus números por debajo, todo el tiempo.",
  },
];

export default function AcercaV2Page() {
  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop max-w-3xl mx-auto flex flex-col gap-6 w-full mt-2 pb-12"
    >
      <div className="flex flex-col gap-1.5">
        <p className="text-xs font-medium tracking-widest uppercase text-on-surface-variant/90">
          Contexia
        </p>
        <h1 className="font-extralight tracking-tight text-white text-[36px] sm:text-[44px] leading-tight">
          ¿Qué es Contexia?
        </h1>
        <p className="text-on-surface-variant text-sm font-normal">
          Tu GPS financiero, en una página
        </p>
      </div>

      <section className="bg-surface-elevated rounded-xl border border-white/10 p-4">
        <p className="font-body-md text-body-md text-white leading-relaxed">
          Contexia es la tecnología que le dice a tu negocio, cada día, cuánta plata real
          tiene, qué le debe a la DIAN y hacia dónde va. Nada de hojas de cálculo ni de
          esperar a fin de mes para enterarte.
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="font-label-caps text-label-caps text-on-surface-variant font-bold uppercase px-1">
          Lo que hace por ti
        </h3>
        <div className="flex flex-col gap-2">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="bg-surface-elevated rounded-xl border border-white/10 p-4 flex items-center gap-3"
            >
              <span className="material-symbols-outlined text-primary">{pillar.icon}</span>
              <div className="flex-1">
                <p className="font-body-md text-body-md text-white font-semibold">
                  {pillar.title}
                </p>
                <p className="font-body-md text-[12px] text-on-surface-variant">
                  {pillar.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <p className="text-center text-[11px] text-on-surface-variant/70 px-2 leading-relaxed">
        Contexia es tecnología, no una firma contable — no firma declaraciones ni estados
        financieros. Cuando eso hace falta, lo hace una contadora matriculada, como Taty.
      </p>
    </div>
  );
}
