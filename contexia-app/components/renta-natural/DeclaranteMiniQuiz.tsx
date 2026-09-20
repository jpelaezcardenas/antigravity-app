"use client";

import { useState } from "react";
import { formatCop } from "@/lib/format";
import {
  estimarDeclarante,
  UMBRAL_CONSUMOS_COP,
} from "@/lib/rentaNaturalCalculations";

const DIAN_CONSULTA_RENTA_URL = "https://consultarenta.dian.gov.co/consultarenta/";

/**
 * Instant, self-reported "¿debo declarar renta?" estimate on the public
 * /renta-natural landing (b2c-social-lead-capture funnel). Deliberately
 * client-side only, no API call, no lead capture of its own — the
 * existing RentaNaturalLandingForm below still owns lead capture.
 *
 * Founder decision (2026-09-20): integrate BOTH our own quick estimate
 * AND a reference link to DIAN's official tool
 * (consultarenta.dian.gov.co) in the same flow — never one instead of
 * the other, since this quiz can't see the visitor's real tax records.
 */
export function DeclaranteMiniQuiz() {
  const [ingresos, setIngresos] = useState("");
  const [patrimonio, setPatrimonio] = useState("");
  const [superoConsumos, setSuperoConsumos] = useState<boolean | null>(null);
  const [mostrarResultado, setMostrarResultado] = useState(false);

  const puedeCalcular =
    ingresos !== "" && patrimonio !== "" && superoConsumos !== null;

  const handleCalcular = () => {
    if (!puedeCalcular) return;
    setMostrarResultado(true);
  };

  const resultado = mostrarResultado
    ? estimarDeclarante({
        ingresosAnuales: Number(ingresos),
        patrimonioBruto: Number(patrimonio),
        superoConsumosOConsignaciones: superoConsumos === true,
      })
    : null;

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-6">
      <div className="flex flex-col gap-1">
        <span className="text-xs font-bold uppercase tracking-widest text-teal-300">
          ¿Debo declarar renta?
        </span>
        <p className="text-sm text-white/70">
          Responde 3 preguntas rápidas para un estimado — luego deja tus datos abajo para que Taty te ayude.
        </p>
      </div>

      {!mostrarResultado && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ingresos_anuales" className="text-sm font-semibold text-white/90">
              ¿Cuánto fueron tus ingresos brutos en el año? (COP)
            </label>
            <input
              id="ingresos_anuales"
              type="number"
              inputMode="numeric"
              min={0}
              value={ingresos}
              onChange={(e) => setIngresos(e.target.value)}
              className="rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-white placeholder-white/40 outline-none focus:border-teal-400"
              placeholder="Ej. 60000000"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="patrimonio_bruto" className="text-sm font-semibold text-white/90">
              ¿Cuánto vale tu patrimonio bruto a 31 de diciembre? (COP)
            </label>
            <input
              id="patrimonio_bruto"
              type="number"
              inputMode="numeric"
              min={0}
              value={patrimonio}
              onChange={(e) => setPatrimonio(e.target.value)}
              className="rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-white placeholder-white/40 outline-none focus:border-teal-400"
              placeholder="Ej. 40000000"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold text-white/90">
              ¿Tus consumos con tarjeta de crédito o consignaciones bancarias superaron {formatCop(UMBRAL_CONSUMOS_COP)} en el año?
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setSuperoConsumos(true)}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-bold transition-colors ${
                  superoConsumos === true
                    ? "bg-teal-400 text-slate-950"
                    : "border border-white/15 bg-black/30 text-white/80 hover:border-teal-400/50"
                }`}
              >
                Sí
              </button>
              <button
                type="button"
                onClick={() => setSuperoConsumos(false)}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-bold transition-colors ${
                  superoConsumos === false
                    ? "bg-teal-400 text-slate-950"
                    : "border border-white/15 bg-black/30 text-white/80 hover:border-teal-400/50"
                }`}
              >
                No
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleCalcular}
            disabled={!puedeCalcular}
            className="mt-1 rounded-lg bg-teal-400 px-4 py-2.5 font-bold text-slate-950 transition-colors hover:bg-teal-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Ver mi estimado →
          </button>
        </div>
      )}

      {resultado && (
        <div className="flex flex-col gap-3">
          <div
            className={`rounded-xl border p-4 ${
              resultado.probableDeclarante
                ? "border-amber-400/40 bg-amber-400/10"
                : "border-teal-400/40 bg-teal-400/10"
            }`}
          >
            <p className="text-sm font-bold text-white">
              {resultado.probableDeclarante
                ? "Probablemente sí debes declarar renta"
                : "Con estos datos, probablemente no estarías obligado a declarar"}
            </p>
            {resultado.probableDeclarante && (
              <p className="mt-1 text-xs text-white/70">
                Superaste el tope en: {resultado.criteriosSuperados.join(", ")}.
              </p>
            )}
            <p className="mt-2 text-xs text-white/60">
              Esto es un estimado basado solo en lo que nos contaste — no reemplaza tu declaración real.
              La DIAN también evalúa compras y consignaciones que no preguntamos aquí.
            </p>
          </div>

          <a
            href={DIAN_CONSULTA_RENTA_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-center text-sm font-semibold text-teal-300 underline underline-offset-2 hover:text-teal-200"
          >
            Verifícalo oficialmente en la DIAN →
          </a>

          <button
            type="button"
            onClick={() => setMostrarResultado(false)}
            className="text-center text-xs text-white/50 hover:text-white/70"
          >
            Volver a calcular
          </button>
        </div>
      )}
    </div>
  );
}
