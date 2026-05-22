"use client";

import type { CapitalData } from "@/lib/types/crearEmpresa";
import { formatCop } from "@/lib/format";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step6CapitalProps {
  data: CapitalData;
  onChange: (next: CapitalData) => void;
}

const QUICK_AMOUNTS = [400_000, 500_000, 600_000, 700_000, 800_000];

export function Step6Capital({ data, onChange }: Step6CapitalProps) {
  const handleTotal = (val: number) => {
    onChange({ ...data, total: Math.max(0, Math.min(val, 800_000)) });
  };

  const handleSuscrito = (pct: number) => {
    const clamped = Math.max(0, Math.min(100, pct));
    onChange({
      ...data,
      suscritoPct: clamped,
      pagadoPct: Math.min(data.pagadoPct, clamped),
    });
  };

  const handlePagado = (pct: number) => {
    const clamped = Math.max(0, Math.min(data.suscritoPct, pct));
    onChange({ ...data, pagadoPct: clamped });
  };

  const suscrito = (data.total * data.suscritoPct) / 100;
  const pagado = (data.total * data.pagadoPct) / 100;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Con cuánta plata arrancas?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Es el capital social inicial de la empresa. No tienes que poner toda esta plata
          hoy — solo lo que vayas a aportar al principio.
        </p>
      </div>

      <TatyTipCard title="Tip de Taty sobre el capital">
        Mientras más alto el capital, más caro el registro en Cámara de Comercio. Para
        arrancar te recomiendo entre <strong className="text-[#2DD4BF]">$400.000 y $800.000
        COP</strong> — es lo más eficiente para minimizar costos de Cámara. Después puedes
        aumentar el capital cuando crezca el negocio. Lo importante es lo que pones de
        verdad como &quot;pagado&quot;.
      </TatyTipCard>

      {/* Total */}
      <div>
        <label
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Capital total de la empresa
        </label>
        <div className="relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant">
            $
          </span>
          <input
            type="number"
            inputMode="numeric"
            value={data.total || ""}
            onChange={(e) => handleTotal(parseInt(e.target.value) || 0)}
            placeholder="1000000"
            className="w-full bg-surface-container border border-white/10 rounded-xl pl-8 pr-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all font-data-mono"
          />
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {QUICK_AMOUNTS.map((amount) => (
            <button
              key={amount}
              type="button"
              onClick={() => handleTotal(amount)}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                data.total === amount
                  ? "bg-[#2DD4BF] text-[#020617]"
                  : "bg-white/[0.05] text-on-surface-variant border border-white/10 hover:bg-white/[0.1]"
              }`}
            >
              {formatCop(amount)}
            </button>
          ))}
        </div>
      </div>

      {/* Suscrito */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Capital suscrito (lo que prometen aportar)
          </label>
          <span
            className="text-sm text-[#2DD4BF] font-bold"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            {data.suscritoPct}% · {formatCop(suscrito)}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          step={1}
          value={data.suscritoPct}
          onChange={(e) => handleSuscrito(parseInt(e.target.value))}
          className="w-full accent-[#2DD4BF]"
        />
      </div>

      {/* Pagado */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Capital pagado hoy
          </label>
          <span
            className="text-sm text-[#8B5CF6] font-bold"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            {data.pagadoPct}% · {formatCop(pagado)}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={data.suscritoPct}
          step={1}
          value={data.pagadoPct}
          onChange={(e) => handlePagado(parseInt(e.target.value))}
          className="w-full accent-[#8B5CF6]"
        />
        <p className="text-[11px] text-on-surface-variant/70 mt-2">
          Lo &quot;pagado&quot; es la plata que pones de verdad ya. El resto puedes meterlo
          después (hasta 2 años).
        </p>
      </div>

      {/* Resumen */}
      <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4 flex flex-col gap-2">
        <div className="flex justify-between text-sm">
          <span className="text-on-surface-variant">Capital total</span>
          <span className="text-white font-bold font-data-mono">
            {formatCop(data.total)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-on-surface-variant">Comprometido (suscrito)</span>
          <span className="text-[#2DD4BF] font-bold font-data-mono">
            {formatCop(suscrito)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-on-surface-variant">Pagado hoy</span>
          <span className="text-[#8B5CF6] font-bold font-data-mono">
            {formatCop(pagado)}
          </span>
        </div>
      </div>
    </div>
  );
}
