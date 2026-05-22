"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type {
  WizardState,
  WizardStep,
  PaymentMethod,
  RepresentanteData,
  CapitalData,
  EmpresaDescripcion,
  ContactoData,
  AccionistaData,
  TipoSociedad,
} from "@/lib/types/crearEmpresa";
import {
  INITIAL_WIZARD_STATE,
  WIZARD_STORAGE_KEY,
  PRICE_CREAR_EMPRESA,
  WIZARD_STEPS_LABELS,
} from "@/lib/types/crearEmpresa";
import {
  validateStep,
  nextStep,
  prevStep,
} from "@/lib/utils/crearEmpresaLogic";
import { formatNombreEmpresaConSufijo } from "@/lib/utils/crearEmpresaLogic";
import { formatCop } from "@/lib/format";
import { Stepper } from "@/components/crear-empresa/Stepper";
import { StepNavigation } from "@/components/crear-empresa/StepNavigation";
import { PriceCard } from "@/components/crear-empresa/PriceCard";
import { Step1Contacto } from "@/components/crear-empresa/steps/Step1Contacto";
import { Step2Estructura } from "@/components/crear-empresa/steps/Step2Estructura";
import { Step3Nombre } from "@/components/crear-empresa/steps/Step3Nombre";
import { Step4Descripcion } from "@/components/crear-empresa/steps/Step4Descripcion";
import { Step5Accionistas } from "@/components/crear-empresa/steps/Step5Accionistas";
import { Step6Capital } from "@/components/crear-empresa/steps/Step6Capital";
import { Step7Representante } from "@/components/crear-empresa/steps/Step7Representante";
import { Step8Pago, EMPTY_COUPON, type CouponState } from "@/components/crear-empresa/steps/Step8Pago";
import { createTransaction, openWompiCheckout } from "@/lib/payments/wompiCheckout";

export default function CrearEmpresaWizardPage() {
  const [state, setState] = useState<WizardState>(INITIAL_WIZARD_STATE);
  const [errorMsg, setErrorMsg] = useState<string | undefined>();
  const [confirmed, setConfirmed] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [savedHint, setSavedHint] = useState(false);
  const [coupon, setCoupon] = useState<CouponState>(EMPTY_COUPON);
  const [paying, setPaying] = useState(false);

  // Hydrate from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(WIZARD_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as WizardState;
        setState(parsed);
      }
    } catch {
      // ignore
    }
    setHydrated(true);
  }, []);

  // Save to localStorage when state changes (after hydration)
  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(state));
      setSavedHint(true);
      const t = setTimeout(() => setSavedHint(false), 1500);
      return () => clearTimeout(t);
    } catch {
      // ignore
    }
  }, [state, hydrated]);

  const update = (patch: Partial<WizardState>) => {
    setState((prev) => ({ ...prev, ...patch }));
    setErrorMsg(undefined);
  };

  const handleNext = async () => {
    const result = validateStep(state.step, state);
    if (!result.ok) {
      setErrorMsg(result.error);
      return;
    }
    setErrorMsg(undefined);
    if (state.step === 8) {
      await handlePay();
      return;
    }
    update({ step: nextStep(state.step) });
  };

  const handlePay = async () => {
    if (paying) return;
    setPaying(true);
    setErrorMsg(undefined);
    try {
      const tx = await createTransaction({
        wizardData: state,
        couponCode: coupon.valid ? coupon.code : null,
      });
      const redirectUrl = `${window.location.origin}/wizard/confirmacion?ref=${encodeURIComponent(tx.reference)}`;
      await openWompiCheckout({
        publicKey: tx.publicKey,
        reference: tx.reference,
        signature: tx.signature,
        amountInCents: tx.amountInCents,
        currency: tx.currency,
        customerEmail: state.contacto.email,
        customerName: state.contacto.nombre,
        customerPhone: state.contacto.telefono,
        redirectUrl,
      });
      // Widget is open. Wompi will redirect to /wizard/confirmacion on completion;
      // that page handles success/failure UI and the localStorage cleanup.
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "No se pudo iniciar el pago");
    } finally {
      setPaying(false);
    }
  };

  const handleBack = () => {
    setErrorMsg(undefined);
    update({ step: prevStep(state.step) });
  };

  const handleReset = () => {
    if (!confirm("¿Empezar de nuevo? Perderás los datos ingresados.")) return;
    try {
      localStorage.removeItem(WIZARD_STORAGE_KEY);
    } catch {
      // ignore
    }
    setState(INITIAL_WIZARD_STATE);
    setErrorMsg(undefined);
  };

  if (confirmed) {
    return <ConfirmationView state={state} />;
  }

  return (
    <>
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl border-b border-white/10 bg-[#020617]/85">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-3">
          <Link href="/" className="flex items-center group" aria-label="Volver a Contexia">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/assets/img/logo_official.png"
              alt="Contexia"
              className="h-14 md:h-16 w-auto object-contain mix-blend-screen scale-110 transition-transform group-hover:scale-115"
            />
          </Link>

          <div className="hidden md:flex items-center gap-4">
            {savedHint && (
              <span
                className="text-[11px] text-[#22C55E] font-bold uppercase tracking-widest flex items-center gap-1"
                style={{ fontFamily: "Rajdhani, sans-serif" }}
              >
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
                Guardado
              </span>
            )}
            <button
              type="button"
              onClick={handleReset}
              className="text-[11px] text-on-surface-variant hover:text-white font-bold uppercase tracking-widest transition-colors"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              Empezar de nuevo
            </button>
          </div>

          <Link
            href="/landing.html"
            className="text-[11px] text-on-surface-variant hover:text-[#2DD4BF] font-bold uppercase tracking-widest transition-colors flex items-center gap-1"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            <span className="material-symbols-outlined text-[16px]">close</span>
            <span className="hidden sm:inline">Salir</span>
          </Link>
        </div>

        {/* Progress strip */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-3">
          <Stepper current={state.step} />
        </div>
      </header>

      {/* Main wizard content */}
      <main className="flex-1">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Step content */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 md:p-7 backdrop-blur-md">
              <StepRenderer state={state} update={update} coupon={coupon} setCoupon={setCoupon} />
            </div>

            <StepNavigation
              onBack={state.step > 1 ? handleBack : undefined}
              onNext={handleNext}
              canGoBack={state.step > 1}
              canGoNext={!paying}
              isFinalStep={state.step === 8}
              nextLabel={
                state.step === 8
                  ? paying
                    ? "Abriendo Wompi…"
                    : `Pagar ${formatCop(coupon.valid ? coupon.finalCop : PRICE_CREAR_EMPRESA)}`
                  : "Siguiente"
              }
              errorMessage={errorMsg}
            />
          </div>

          {/* Sticky sidebar (desktop) */}
          <aside className="hidden lg:flex flex-col gap-4 sticky top-[180px] self-start">
            <PriceCard variant="full" />
          </aside>

          {/* Mobile compact price */}
          <div className="lg:hidden order-first">
            <PriceCard variant="compact" />
          </div>
        </div>
      </main>

      <footer className="border-t border-white/5 py-4 mt-6">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p
            className="text-[10px] text-on-surface-variant/60 uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Contexia · Tu amiga contadora · 24/7
          </p>
        </div>
      </footer>
    </>
  );
}

function StepRenderer({
  state,
  update,
  coupon,
  setCoupon,
}: {
  state: WizardState;
  update: (patch: Partial<WizardState>) => void;
  coupon: CouponState;
  setCoupon: (c: CouponState) => void;
}) {
  switch (state.step) {
    case 1:
      return (
        <Step1Contacto
          data={state.contacto}
          onChange={(c: ContactoData) => update({ contacto: c })}
        />
      );
    case 2:
      return (
        <Step2Estructura
          value={state.tipoSociedad}
          onChange={(t: TipoSociedad) => update({ tipoSociedad: t })}
        />
      );
    case 3:
      return (
        <Step3Nombre
          nombre={state.nombreEmpresa}
          tipoSociedad={state.tipoSociedad}
          disponible={state.nombreDisponible}
          onChange={(n: string, d: boolean | null) =>
            update({ nombreEmpresa: n, nombreDisponible: d })
          }
        />
      );
    case 4:
      return (
        <Step4Descripcion
          data={state.descripcion}
          onChange={(d: EmpresaDescripcion) => update({ descripcion: d })}
        />
      );
    case 5:
      return (
        <Step5Accionistas
          accionistas={state.accionistas}
          onChange={(a: AccionistaData[]) => update({ accionistas: a })}
        />
      );
    case 6:
      return (
        <Step6Capital
          data={state.capital}
          onChange={(c: CapitalData) => update({ capital: c })}
        />
      );
    case 7:
      return (
        <Step7Representante
          data={state.representante}
          accionistas={state.accionistas}
          onChange={(r: RepresentanteData) => update({ representante: r })}
        />
      );
    case 8:
      return (
        <Step8Pago
          state={state}
          onChangePayment={(method: PaymentMethod) => update({ paymentMethod: method })}
          onAcceptTerms={(accepted: boolean) => update({ acceptedTerms: accepted })}
          coupon={coupon}
          onCouponChange={setCoupon}
        />
      );
    default:
      return null;
  }
}

function ConfirmationView({ state }: { state: WizardState }) {
  const fullName = formatNombreEmpresaConSufijo(
    state.nombreEmpresa,
    state.tipoSociedad,
  );
  const whatsappMsg = encodeURIComponent(
    `Hola Taty, acabo de iniciar la creación de mi empresa "${fullName}" en Contexia. Necesito que me confirmes los siguientes pasos para el pago de ${formatCop(PRICE_CREAR_EMPRESA)}. Mi correo: ${state.contacto.email}`,
  );
  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-lg w-full bg-gradient-to-br from-[#2DD4BF]/10 to-[#8B5CF6]/10 border border-[#2DD4BF]/40 rounded-3xl p-8 backdrop-blur-xl shadow-[0_0_60px_rgba(45,212,191,0.2)] text-center flex flex-col gap-5">
        <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-tr from-[#2DD4BF] to-[#8B5CF6] flex items-center justify-center shadow-[0_0_30px_rgba(45,212,191,0.5)]">
          <span className="material-symbols-outlined text-white text-[40px]">
            celebration
          </span>
        </div>

        <div>
          <h1
            className="text-3xl font-black text-white"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            ¡Listo, {state.contacto.nombre.split(" ")[0]}!
          </h1>
          <p className="text-on-surface-variant mt-2">
            Recibimos tu solicitud para crear{" "}
            <strong className="text-[#2DD4BF]">{fullName}</strong>. Taty te contactará por
            WhatsApp en los próximos minutos para confirmar el pago de{" "}
            <strong className="text-white">{formatCop(PRICE_CREAR_EMPRESA)}</strong>.
          </p>
        </div>

        <a
          href={`https://wa.me/573018948151?text=${whatsappMsg}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-[#25D366] text-white font-bold shadow-[0_0_24px_rgba(37,211,102,0.4)] hover:shadow-[0_0_32px_rgba(37,211,102,0.6)] transition-all"
        >
          <svg
            className="w-5 h-5 fill-white"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
          </svg>
          Continuar por WhatsApp con Taty
        </a>

        <p className="text-[12px] text-on-surface-variant/70">
          También te enviamos un correo a <strong className="text-white">{state.contacto.email}</strong> con el resumen.
        </p>

        <Link
          href="/landing.html"
          className="text-[11px] text-on-surface-variant hover:text-[#2DD4BF] uppercase tracking-widest font-bold"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Volver al inicio
        </Link>
      </div>
    </main>
  );
}
