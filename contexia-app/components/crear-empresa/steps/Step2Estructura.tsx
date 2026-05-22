"use client";

import type { TipoSociedad } from "@/lib/types/crearEmpresa";
import { TIPOS_SOCIEDAD } from "@/lib/mock/crearEmpresa";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step2EstructuraProps {
  value: TipoSociedad | null;
  onChange: (next: TipoSociedad) => void;
}

export function Step2Estructura({ value, onChange }: Step2EstructuraProps) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Qué tipo de empresa?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Es la base legal de tu negocio. Si dudas, te recomiendo la SAS — es la más usada en
          Colombia.
        </p>
      </div>

      <TatyTipCard title="¿Por qué casi todos eligen SAS?">
        Porque te protege a ti como persona. Si la empresa tiene problemas, tu plata
        personal queda separada. Además es flexible: puedes empezar solo, agregar socios
        después, vender acciones, etc.
      </TatyTipCard>

      <div className="flex flex-col gap-3">
        {TIPOS_SOCIEDAD.map((tipo) => {
          const selected = value === tipo.id;
          return (
            <button
              key={tipo.id}
              type="button"
              onClick={() => onChange(tipo.id)}
              className={`text-left rounded-xl p-5 border transition-all relative overflow-hidden ${
                selected
                  ? "bg-gradient-to-br from-[#2DD4BF]/15 to-[#8B5CF6]/5 border-[#2DD4BF] shadow-[0_0_24px_rgba(45,212,191,0.25)]"
                  : "bg-white/[0.03] border-white/10 hover:border-[#2DD4BF]/40 hover:bg-white/[0.05]"
              }`}
            >
              {tipo.recommended && (
                <span className="absolute top-3 right-3 px-2 py-0.5 bg-[#8B5CF6]/20 border border-[#8B5CF6]/40 rounded-full text-[9px] text-[#8B5CF6] font-bold uppercase tracking-widest">
                  Recomendado
                </span>
              )}

              <div className="flex items-start gap-3">
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all ${
                    selected
                      ? "border-[#2DD4BF] bg-[#2DD4BF]"
                      : "border-white/30"
                  }`}
                >
                  {selected && (
                    <span className="material-symbols-outlined text-[16px] text-[#020617]">
                      check
                    </span>
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <h3
                      className={`text-xl font-black ${
                        selected ? "text-[#2DD4BF]" : "text-white"
                      }`}
                      style={{ fontFamily: "Orbitron, sans-serif" }}
                    >
                      {tipo.label}
                    </h3>
                    <span className="text-[11px] text-on-surface-variant uppercase tracking-widest font-bold">
                      {tipo.subtitle}
                    </span>
                  </div>
                  <p className="text-sm text-on-surface mt-2 leading-relaxed">
                    {tipo.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
