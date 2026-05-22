"use client";

import type { ContactoData } from "@/lib/types/crearEmpresa";
import { formatTelefono } from "@/lib/utils/crearEmpresaLogic";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step1ContactoProps {
  data: ContactoData;
  onChange: (next: ContactoData) => void;
}

export function Step1Contacto({ data, onChange }: Step1ContactoProps) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Cómo te contactamos?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Te mandamos el código por correo y te avisamos del avance por WhatsApp.
        </p>
      </div>

      <TatyTipCard title="¿Por qué te pido estos datos?">
        Para enviarte el código de verificación, los certificados de tu empresa y mantenerte
        informado de cada paso. Tu información está segura conmigo — no la compartimos.
      </TatyTipCard>

      <div className="flex flex-col gap-4">
        {/* Nombre */}
        <div>
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Tu nombre completo
          </label>
          <input
            type="text"
            value={data.nombre}
            onChange={(e) => onChange({ ...data, nombre: e.target.value })}
            placeholder="Juan Pérez"
            className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
          />
        </div>

        {/* Teléfono */}
        <div>
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Tu WhatsApp
          </label>
          <div className="flex gap-2">
            <div className="bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface flex items-center font-data-mono text-sm">
              +57
            </div>
            <input
              type="tel"
              inputMode="numeric"
              value={data.telefono}
              onChange={(e) =>
                onChange({ ...data, telefono: formatTelefono(e.target.value) })
              }
              placeholder="300 123 4567"
              className="flex-1 bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
            />
          </div>
        </div>

        {/* Email */}
        <div>
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Tu correo
          </label>
          <input
            type="email"
            value={data.email}
            onChange={(e) => onChange({ ...data, email: e.target.value })}
            placeholder="tu@correo.com"
            className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
          />
          <p className="text-[11px] text-on-surface-variant/70 mt-2">
            Te enviaremos un código de 6 dígitos para confirmar.
          </p>
        </div>
      </div>
    </div>
  );
}
