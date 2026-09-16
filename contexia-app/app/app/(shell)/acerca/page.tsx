// "¿Qué es Contexia?" — reached from Config's help section. Static, brand copy only (no
// data-bound content, per contexia-app/CLAUDE.md's mock-first charter), sourced from
// .antigravity/GROUND_TRUTH.md so it never overstates what Contexia is: a technology company
// (Entidad B), never a regulated accounting firm — see the closing note below.

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

export default function AcercaPage() {
  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-3xl mx-auto flex flex-col gap-6 w-full mt-2 pb-12">
      <section className="flex flex-col gap-1">
        <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-white">
          ¿Qué es Contexia?
        </h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Tu GPS financiero, en una página
        </p>
      </section>

      <section className="bg-surface-elevated rounded-xl border border-white/10 p-4">
        <p className="font-body-md text-body-md text-white leading-relaxed">
          Contexia es la tecnología que le dice a tu negocio, cada día, cuánta plata real
          tiene, qué le debe a la DIAN y hacia dónde va. Nada de hojas de cálculo ni de
          esperar a fin de mes para enterarte.
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <h3
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest px-1"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
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
