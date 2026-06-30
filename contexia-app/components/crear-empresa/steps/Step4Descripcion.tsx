"use client";

import type { EmpresaDescripcion } from "@/lib/types/crearEmpresa";
import { CIUDADES_COLOMBIA, CIIU_SUGERIDOS } from "@/lib/mock/crearEmpresa";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step4DescripcionProps {
  data: EmpresaDescripcion;
  onChange: (next: EmpresaDescripcion) => void;
}

export function Step4Descripcion({ data, onChange }: Step4DescripcionProps) {
  const handleCiudad = (ciudadValue: string) => {
    const found = CIUDADES_COLOMBIA.find((c) => c.value === ciudadValue);
    onChange({
      ...data,
      ciudad: found?.label || "",
      departamento: found?.departamento || "",
    });
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Qué hace tu empresa?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Cuéntanos en pocas palabras a qué se va a dedicar y dónde va a quedar.
        </p>
      </div>

      <div>
        <label
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Actividad económica
        </label>
        <textarea
          value={data.actividad}
          onChange={(e) => onChange({ ...data, actividad: e.target.value })}
          placeholder="Ejemplo: Vendemos ropa por internet a clientes en toda Colombia."
          rows={3}
          className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all resize-none"
        />
        <p className="text-[11px] text-on-surface-variant/70 mt-1">
          Mínimo 20 letras. Sin enredos, explícalo como se lo dirías a un amigo.
        </p>
      </div>

      <div>
        <label
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Código CIIU (opcional — te lo sugerimos)
        </label>
        <select
          value={data.ciiu || ""}
          onChange={(e) => onChange({ ...data, ciiu: e.target.value })}
          className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
        >
          <option value="">-- Elige el más cercano a lo que haces --</option>
          {CIIU_SUGERIDOS.map((c) => (
            <option key={c.code} value={c.code} className="bg-[#0F172A]">
              {c.code} · {c.label}
            </option>
          ))}
        </select>
        <p className="text-[11px] text-on-surface-variant/70 mt-1">
          Es el código que la DIAN usa para clasificar tu actividad. Si no lo conoces, no te
          preocupes — elegimos el más cercano.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Ciudad
          </label>
          <select
            value={
              CIUDADES_COLOMBIA.find((c) => c.label === data.ciudad)?.value || ""
            }
            onChange={(e) => handleCiudad(e.target.value)}
            className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
          >
            <option value="">-- Selecciona --</option>
            {CIUDADES_COLOMBIA.map((c) => (
              <option key={c.value} value={c.value} className="bg-[#0F172A]">
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Dirección
          </label>
          <input
            type="text"
            value={data.direccion}
            onChange={(e) => onChange({ ...data, direccion: e.target.value })}
            placeholder="Calle 100 # 15-20"
            className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
          />
        </div>
      </div>

      <TatyTipCard title="¿Para qué la dirección?">
        Es la dirección comercial oficial de tu empresa. Puede ser tu casa, una oficina o un
        coworking. Después puedes cambiarla cuando quieras.
      </TatyTipCard>
    </div>
  );
}
