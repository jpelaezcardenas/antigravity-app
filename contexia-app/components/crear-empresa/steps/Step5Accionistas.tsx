"use client";

import type { AccionistaData } from "@/lib/types/crearEmpresa";
import {
  createEmptyAccionista,
  formatCedula,
} from "@/lib/utils/crearEmpresaLogic";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step5AccionistasProps {
  accionistas: AccionistaData[];
  onChange: (next: AccionistaData[]) => void;
}

export function Step5Accionistas({ accionistas, onChange }: Step5AccionistasProps) {
  const totalPct = accionistas.reduce((s, a) => s + (a.participacion || 0), 0);

  const handleAdd = () => {
    onChange([...accionistas, createEmptyAccionista()]);
  };

  const handleRemove = (id: string) => {
    onChange(accionistas.filter((a) => a.id !== id));
  };

  const handleUpdate = (id: string, patch: Partial<AccionistaData>) => {
    onChange(
      accionistas.map((a) => (a.id === id ? { ...a, ...patch } : a)),
    );
  };

  const handleSplit = () => {
    if (accionistas.length === 0) return;
    const each = Math.floor(10000 / accionistas.length) / 100;
    const remainder = 100 - each * accionistas.length;
    const updated = accionistas.map((a, i) => ({
      ...a,
      participacion: i === 0 ? each + remainder : each,
    }));
    onChange(updated);
  };

  const pctOk = Math.abs(totalPct - 100) < 0.01 && accionistas.length > 0;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Quiénes son los socios?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Agrega a todas las personas que tendrán parte de la empresa. La suma debe ser 100%.
        </p>
      </div>

      <TatyTipCard title="¿Cómo reparto las participaciones?">
        Si son socios iguales, divide 100% entre todos. Por ejemplo: 2 socios = 50% cada uno.
        Si alguien aporta más, puedes darle más participación. Más adelante puedes vender
        o transferir acciones.
      </TatyTipCard>

      <div className="flex flex-col gap-3">
        {accionistas.map((acc, idx) => (
          <div
            key={acc.id}
            className="bg-surface-elevated border border-white/10 rounded-xl p-4 flex flex-col gap-3"
          >
            <div className="flex items-center justify-between">
              <span
                className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest"
                style={{ fontFamily: "Rajdhani, sans-serif" }}
              >
                Socio #{idx + 1}
              </span>
              <button
                type="button"
                onClick={() => handleRemove(acc.id)}
                className="text-[#EF4444] hover:bg-[#EF4444]/10 rounded-lg p-1 transition-colors"
                aria-label="Eliminar"
              >
                <span className="material-symbols-outlined text-[18px]">delete</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="text"
                value={acc.nombre}
                onChange={(e) => handleUpdate(acc.id, { nombre: e.target.value })}
                placeholder="Nombre completo"
                className="bg-surface-container border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50"
              />
              <input
                type="text"
                inputMode="numeric"
                value={acc.cedula}
                onChange={(e) =>
                  handleUpdate(acc.id, { cedula: formatCedula(e.target.value) })
                }
                placeholder="Cédula"
                className="bg-surface-container border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50"
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-on-surface-variant flex-shrink-0">
                Participación
              </span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                value={acc.participacion || ""}
                onChange={(e) =>
                  handleUpdate(acc.id, {
                    participacion: Math.max(0, Math.min(100, parseFloat(e.target.value) || 0)),
                  })
                }
                placeholder="0"
                className="w-24 bg-surface-container border border-white/10 rounded-lg px-3 py-2 text-white text-sm text-right placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50"
              />
              <span className="text-sm text-on-surface-variant">%</span>
            </div>
          </div>
        ))}

        <button
          type="button"
          onClick={handleAdd}
          className="flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-dashed border-[#2DD4BF]/40 bg-[#2DD4BF]/5 text-[#2DD4BF] hover:bg-[#2DD4BF]/10 hover:border-[#2DD4BF]/60 transition-all font-bold"
        >
          <span className="material-symbols-outlined">add</span>
          Agregar socio
        </button>

        {accionistas.length >= 2 && (
          <button
            type="button"
            onClick={handleSplit}
            className="text-[12px] text-[#2DD4BF] hover:underline self-center"
          >
            Repartir igual entre todos ({(100 / accionistas.length).toFixed(1)}% c/u)
          </button>
        )}
      </div>

      {accionistas.length > 0 && (
        <div
          className={`flex items-center justify-between p-4 rounded-xl border ${
            pctOk
              ? "bg-[#22C55E]/10 border-[#22C55E]/30"
              : "bg-[#FACC15]/10 border-[#FACC15]/30"
          }`}
        >
          <span
            className={`text-sm font-bold ${
              pctOk ? "text-[#22C55E]" : "text-[#FACC15]"
            }`}
          >
            {pctOk ? "✓ Suma 100% perfecto" : `Total: ${totalPct.toFixed(1)}% (debe ser 100%)`}
          </span>
          {!pctOk && accionistas.length >= 1 && (
            <button
              type="button"
              onClick={handleSplit}
              className="text-xs text-[#FACC15] hover:underline"
            >
              Auto-ajustar
            </button>
          )}
        </div>
      )}
    </div>
  );
}
