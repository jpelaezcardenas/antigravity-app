"use client";

import { useState } from "react";
import type { WizardState, PaymentMethod } from "@/lib/types/crearEmpresa";
import { PRICE_CREAR_EMPRESA } from "@/lib/types/crearEmpresa";
import { TIPOS_SOCIEDAD, PAYMENT_METHODS } from "@/lib/mock/crearEmpresa";
import { formatNombreEmpresaConSufijo } from "@/lib/utils/crearEmpresaLogic";
import { formatCop } from "@/lib/format";
import { PriceCard } from "@/components/crear-empresa/PriceCard";
import { validateCoupon } from "@/lib/payments/wompiCheckout";

export interface CouponState {
  code: string;
  valid: boolean | null;
  discountCop: number;
  description: string | null;
  finalCop: number;
}

export const EMPTY_COUPON: CouponState = {
  code: "",
  valid: null,
  discountCop: 0,
  description: null,
  finalCop: PRICE_CREAR_EMPRESA,
};

interface Step8PagoProps {
  state: WizardState;
  onChangePayment: (method: PaymentMethod) => void;
  onAcceptTerms: (accepted: boolean) => void;
  coupon: CouponState;
  onCouponChange: (c: CouponState) => void;
}

export function Step8Pago({
  state,
  onChangePayment,
  onAcceptTerms,
  coupon,
  onCouponChange,
}: Step8PagoProps) {
  const [couponOpen, setCouponOpen] = useState(coupon.valid === true);
  const [couponLoading, setCouponLoading] = useState(false);

  const onApplyCoupon = async () => {
    const code = coupon.code.trim();
    if (!code) {
      onCouponChange({ ...EMPTY_COUPON });
      return;
    }
    setCouponLoading(true);
    try {
      const res = await validateCoupon(code);
      onCouponChange({
        code,
        valid: res.valid,
        discountCop: res.discountCop,
        description: res.description,
        finalCop: res.finalCop,
      });
    } finally {
      setCouponLoading(false);
    }
  };

  const tipoSociedad = TIPOS_SOCIEDAD.find((t) => t.id === state.tipoSociedad);
  const fullName = formatNombreEmpresaConSufijo(state.nombreEmpresa, state.tipoSociedad);

  const representanteNombre =
    state.representante.origen === "socio"
      ? state.accionistas.find((a) => a.id === state.representante.socioId)?.nombre ||
        "(no seleccionado)"
      : state.representante.nombre || "(sin nombre)";

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Resumen y pago
        </h2>
        <p className="text-on-surface-variant mt-1">
          Revisa que todo esté correcto y elige cómo quieres pagar.
        </p>
      </div>

      {/* Resumen */}
      <div className="bg-surface-elevated border border-white/10 rounded-2xl p-5 flex flex-col gap-4">
        {/* Empresa */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-[#2DD4BF] text-[18px]">
              business
            </span>
            <span
              className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              Tu empresa
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-on-surface-variant">Nombre:</span>
            <span className="text-white font-bold text-right">{fullName || "—"}</span>
            <span className="text-on-surface-variant">Tipo:</span>
            <span className="text-white text-right">{tipoSociedad?.label || "—"}</span>
            <span className="text-on-surface-variant">Ubicación:</span>
            <span className="text-white text-right">
              {state.descripcion.ciudad
                ? `${state.descripcion.ciudad}, ${state.descripcion.departamento}`
                : "—"}
            </span>
          </div>
        </div>

        <div className="border-t border-white/5" />

        {/* Capital */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-[#2DD4BF] text-[18px]">
              payments
            </span>
            <span
              className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              Capital
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-on-surface-variant">Total:</span>
            <span className="text-white text-right font-data-mono">
              {formatCop(state.capital.total)}
            </span>
            <span className="text-on-surface-variant">Suscrito:</span>
            <span className="text-white text-right font-data-mono">
              {formatCop((state.capital.total * state.capital.suscritoPct) / 100)}
            </span>
            <span className="text-on-surface-variant">Pagado hoy:</span>
            <span className="text-[#2DD4BF] text-right font-data-mono font-bold">
              {formatCop((state.capital.total * state.capital.pagadoPct) / 100)}
            </span>
          </div>
        </div>

        <div className="border-t border-white/5" />

        {/* Socios */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-[#2DD4BF] text-[18px]">
              group
            </span>
            <span
              className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              Socios ({state.accionistas.length})
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            {state.accionistas.map((a) => (
              <div key={a.id} className="flex justify-between text-sm">
                <span className="text-white">{a.nombre || "(sin nombre)"}</span>
                <span className="text-[#2DD4BF] font-data-mono">{a.participacion}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-white/5" />

        {/* Representante */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-[#2DD4BF] text-[18px]">
              badge
            </span>
            <span
              className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              Representante legal
            </span>
          </div>
          <p className="text-sm text-white">{representanteNombre}</p>
        </div>
      </div>

      {/* Precio */}
      <PriceCard variant="full" />

      {/* Métodos de pago */}
      <div>
        <h3
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest mb-3"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Cómo quieres pagar?
        </h3>
        <div className="flex flex-col gap-2">
          {PAYMENT_METHODS.map((method) => {
            const selected = state.paymentMethod === method.id;
            return (
              <button
                key={method.id}
                type="button"
                onClick={() => onChangePayment(method.id as PaymentMethod)}
                className={`flex items-center gap-3 p-4 rounded-xl border text-left transition-all ${
                  selected
                    ? "bg-[#2DD4BF]/10 border-[#2DD4BF] shadow-[0_0_16px_rgba(45,212,191,0.2)]"
                    : "bg-white/[0.03] border-white/10 hover:border-[#2DD4BF]/40 hover:bg-white/[0.05]"
                }`}
              >
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    selected ? "bg-[#2DD4BF]/20" : "bg-white/5"
                  }`}
                >
                  <span
                    className={`material-symbols-outlined ${
                      selected ? "text-[#2DD4BF]" : "text-on-surface-variant"
                    }`}
                  >
                    {method.icon}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-bold">{method.label}</p>
                  <p className="text-[12px] text-on-surface-variant">
                    {method.subtitle}
                  </p>
                </div>
                {method.logos && (
                  <div className="hidden md:flex items-center gap-1 text-[10px] text-on-surface-variant/60">
                    {method.logos.map((l) => (
                      <span key={l} className="px-1.5 py-0.5 rounded bg-white/5">
                        {l}
                      </span>
                    ))}
                  </div>
                )}
                <span
                  className={`material-symbols-outlined ${
                    selected ? "text-[#2DD4BF]" : "text-on-surface-variant/40"
                  }`}
                >
                  chevron_right
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Términos */}
      <label className="flex items-start gap-3 cursor-pointer bg-white/[0.03] border border-white/10 rounded-xl p-4">
        <input
          type="checkbox"
          checked={state.acceptedTerms}
          onChange={(e) => onAcceptTerms(e.target.checked)}
          className="mt-0.5 w-5 h-5 accent-[#2DD4BF] cursor-pointer flex-shrink-0"
        />
        <span className="text-[13px] text-on-surface leading-relaxed">
          Acepto los <span className="text-[#2DD4BF] underline">términos y condiciones</span>{" "}
          y entiendo que los costos de Cámara de Comercio y firma electrónica se pagan
          aparte. Autorizo a Taty a procesar mi solicitud de constitución.
        </span>
      </label>

      {/* Timeline: 5 días hábiles */}
      <div className="bg-gradient-to-r from-[#22C55E]/10 to-[#2DD4BF]/10 border border-[#22C55E]/30 rounded-xl p-4 flex items-center gap-3 backdrop-blur-md">
        <div className="w-10 h-10 rounded-full bg-[#22C55E]/20 flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-[#22C55E]">schedule</span>
        </div>
        <div className="flex-1">
          <p
            className="text-[10px] text-[#22C55E] font-bold uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Tu empresa lista en
          </p>
          <p className="text-base text-white font-bold">
            5 días hábiles desde el pago
          </p>
          <p className="text-[11px] text-on-surface-variant mt-0.5">
            100% digital vía VUE — sin notaría ni filas
          </p>
        </div>
      </div>

      <div className="bg-[#020617]/60 border border-[#2DD4BF]/20 rounded-xl p-4 flex items-center gap-3 backdrop-blur-md">
        <span className="material-symbols-outlined text-[#2DD4BF]">verified_user</span>
        <p className="text-[12px] text-on-surface-variant">
          Pago 100% seguro procesado por <strong className="text-white">Wompi</strong>.
          Recibirás un correo con la confirmación y los siguientes pasos.
        </p>
      </div>

      {/* Cupón */}
      <div className="bg-white/[0.02] border border-white/10 rounded-xl">
        <button
          type="button"
          onClick={() => setCouponOpen((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 text-left"
        >
          <span className="flex items-center gap-2 text-[12px] text-on-surface-variant">
            <span className="material-symbols-outlined text-[18px] text-[#8B5CF6]">local_offer</span>
            {coupon.valid ? (
              <span className="text-[#22C55E] font-bold">
                Cupón {coupon.code} aplicado — {formatCop(coupon.discountCop)} de descuento
              </span>
            ) : (
              <span>¿Tienes un código de descuento?</span>
            )}
          </span>
          <span className={`material-symbols-outlined text-on-surface-variant transition-transform ${couponOpen ? "rotate-180" : ""}`}>
            expand_more
          </span>
        </button>
        {couponOpen && (
          <div className="px-4 pb-4 flex flex-col gap-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={coupon.code}
                onChange={(e) =>
                  onCouponChange({ ...coupon, code: e.target.value.toUpperCase(), valid: null, discountCop: 0, finalCop: PRICE_CREAR_EMPRESA, description: null })
                }
                placeholder="LANZAMIENTO50"
                className="flex-1 bg-white/[0.04] border border-white/10 focus:border-[#2DD4BF] rounded-lg px-3 py-2 text-sm text-white outline-none placeholder:text-on-surface-variant/50 font-data-mono"
              />
              <button
                type="button"
                onClick={onApplyCoupon}
                disabled={couponLoading || !coupon.code.trim()}
                className="px-4 py-2 rounded-lg bg-[#2DD4BF]/15 border border-[#2DD4BF]/40 text-[#2DD4BF] font-bold text-sm hover:bg-[#2DD4BF]/25 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {couponLoading ? "..." : "Aplicar"}
              </button>
            </div>
            {coupon.valid === false && (
              <p className="text-[12px] text-[#ef4444]">Cupón no válido o expirado.</p>
            )}
            {coupon.valid === true && coupon.description && (
              <p className="text-[12px] text-[#22C55E]">✓ {coupon.description}</p>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between bg-gradient-to-r from-[#2DD4BF]/10 to-[#8B5CF6]/10 border border-[#2DD4BF]/30 rounded-2xl p-4">
        <div>
          <p
            className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Total a pagar
          </p>
          {coupon.valid && coupon.discountCop > 0 ? (
            <div className="flex items-baseline gap-2">
              <p
                className="text-2xl font-black text-white"
                style={{ fontFamily: "Orbitron, sans-serif" }}
              >
                {formatCop(coupon.finalCop)} COP
              </p>
              <p className="text-sm line-through text-on-surface-variant/60 font-data-mono">
                {formatCop(PRICE_CREAR_EMPRESA)}
              </p>
            </div>
          ) : (
            <p
              className="text-2xl font-black text-white"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              {formatCop(PRICE_CREAR_EMPRESA)} COP
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-[10px] text-on-surface-variant">IVA incluido</p>
          <p className="text-[10px] text-[#22C55E] font-bold">✓ Pago único</p>
        </div>
      </div>
    </div>
  );
}
