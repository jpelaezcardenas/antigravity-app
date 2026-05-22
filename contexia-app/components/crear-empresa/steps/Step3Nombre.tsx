"use client";

import { useState } from "react";
import type { TipoSociedad } from "@/lib/types/crearEmpresa";
import { checkNombreDisponibleMock } from "@/lib/mock/crearEmpresa";
import { formatNombreEmpresaConSufijo } from "@/lib/utils/crearEmpresaLogic";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step3NombreProps {
  nombre: string;
  tipoSociedad: TipoSociedad | null;
  disponible: boolean | null;
  onChange: (nombre: string, disponible: boolean | null) => void;
}

export function Step3Nombre({
  nombre,
  tipoSociedad,
  disponible,
  onChange,
}: Step3NombreProps) {
  const [checking, setChecking] = useState(false);

  const handleNameChange = (next: string) => {
    onChange(next, null); // reset disponible
  };

  const handleCheck = () => {
    if (!nombre.trim() || nombre.trim().length < 4) return;
    setChecking(true);
    setTimeout(() => {
      const ok = checkNombreDisponibleMock(nombre);
      onChange(nombre, ok);
      setChecking(false);
    }, 800);
  };

  const fullName = formatNombreEmpresaConSufijo(nombre, tipoSociedad);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Cómo se va a llamar tu empresa?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Escribe el nombre que quieres y verificamos si está disponible.
        </p>
      </div>

      <div>
        <label
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Nombre de la empresa
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={nombre}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="Mi Empresa"
            className="flex-1 bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
          />
          <button
            type="button"
            onClick={handleCheck}
            disabled={checking || !nombre.trim() || nombre.trim().length < 4}
            className="px-4 py-3 rounded-xl bg-[#2DD4BF] text-[#020617] font-bold hover:bg-[#14B8A6] transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {checking ? "Buscando..." : "Verificar"}
          </button>
        </div>

        {/* Estado de disponibilidad */}
        {disponible === true && (
          <div className="mt-3 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-xl px-4 py-2.5 flex items-center gap-2">
            <span className="material-symbols-outlined text-[#22C55E] text-[18px]">
              check_circle
            </span>
            <span className="text-sm text-[#22C55E] font-medium">
              ¡Excelente! Este nombre está disponible.
            </span>
          </div>
        )}
        {disponible === false && (
          <div className="mt-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl px-4 py-2.5 flex items-center gap-2">
            <span className="material-symbols-outlined text-[#EF4444] text-[18px]">
              cancel
            </span>
            <span className="text-sm text-[#EF4444] font-medium">
              Este nombre no está disponible. Prueba con otra opción.
            </span>
          </div>
        )}
      </div>

      {/* Preview con sufijo */}
      {nombre.trim() && (
        <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4">
          <p
            className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest mb-1"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Tu empresa se llamará
          </p>
          <p
            className="text-xl text-[#2DD4BF] font-black"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            {fullName || nombre}
          </p>
        </div>
      )}

      <TatyTipCard title="Tips para el nombre">
        Evita palabras como &quot;Banco&quot;, &quot;Estado&quot; o &quot;Nacional&quot; (son
        restringidas). Mejor algo corto y fácil de recordar. Si quieres, puedes registrar
        también el dominio web después.
      </TatyTipCard>
    </div>
  );
}
