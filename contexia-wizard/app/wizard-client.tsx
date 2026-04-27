"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useWizardStore } from "@/lib/store";
import WizardHeader from "@/components/layout/WizardHeader";
import WizardFooter from "@/components/layout/WizardFooter";
import TatyFloat from "@/components/layout/TatyFloat";
import Stepper from "@/components/wizard/Stepper";
import Step1Solicitante from "@/components/wizard/steps/Step1Solicitante";
import Step2Empresa from "@/components/wizard/steps/Step2Empresa";
import Step3Sociedad from "@/components/wizard/steps/Step3Sociedad";
import Step4Financiera from "@/components/wizard/steps/Step4Financiera";
import Step5Contable from "@/components/wizard/steps/Step5Contable";
import Step6Administrativa from "@/components/wizard/steps/Step6Administrativa";
import Step7Digital from "@/components/wizard/steps/Step7Digital";
import Step8Diagnostico from "@/components/wizard/steps/Step8Diagnostico";

// ─── Hero banner (pre-step-1) ───────────────────────────────
function WizardHero({ onStart }: { onStart: () => void }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "4rem 1.5rem 3rem",
        maxWidth: "740px",
        margin: "0 auto",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "#e8f7f3",
          color: "#00a878",
          fontWeight: 700,
          fontSize: "0.875rem",
          padding: "0.375rem 0.875rem",
          borderRadius: "999px",
          marginBottom: "1.5rem",
        }}
      >
        🔍 Shadow Audit — Gratis &amp; Sin compromiso
      </div>
      <h1
        style={{
          fontSize: "clamp(2rem, 5vw, 2.75rem)",
          fontWeight: 800,
          color: "#0a2540",
          lineHeight: 1.2,
          margin: "0 0 1rem",
        }}
      >
        ¿Tu empresa paga más
        <br />
        impuestos de lo que debe?
      </h1>
      <p
        style={{
          color: "#475569",
          fontSize: "1.0625rem",
          lineHeight: 1.7,
          margin: "0 0 2.5rem",
          maxWidth: "560px",
          marginLeft: "auto",
          marginRight: "auto",
        }}
      >
        Responde 7 preguntas y en menos de 5 minutos te mostramos cuánto
        pagarías en <strong>Régimen Simple vs Ordinario</strong>, tus riesgos
        DIAN y un plan de acción concreto.
      </p>

      {/* Proof points */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "1.5rem",
          flexWrap: "wrap",
          marginBottom: "2.5rem",
        }}
      >
        {[
          { icon: "⚡", text: "5 minutos" },
          { icon: "🔒", text: "100% confidencial" },
          { icon: "🎯", text: "Basado en UVT 2026" },
          { icon: "💡", text: "Plan de acción real" },
        ].map((p) => (
          <div
            key={p.text}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              color: "#64748b",
              fontSize: "0.9375rem",
            }}
          >
            <span>{p.icon}</span>
            <span>{p.text}</span>
          </div>
        ))}
      </div>

      <button
        onClick={onStart}
        className="ctx-btn-primary"
        style={{ fontSize: "1.0625rem", padding: "1rem 3rem", borderRadius: "12px" }}
      >
        Hacer mi diagnóstico gratuito →
      </button>

      <p style={{ color: "#94a3b8", fontSize: "0.875rem", marginTop: "1.25rem" }}>
        Sin tarjeta de crédito. Sin spam. Solo insights reales.
      </p>

      {/* Trust logos row */}
      <div
        style={{
          marginTop: "3rem",
          paddingTop: "2rem",
          borderTop: "1px solid #e2e8f0",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          alignItems: "center",
        }}
      >
        <p style={{ color: "#94a3b8", fontSize: "0.8125rem" }}>
          Cálculos basados en normativa vigente
        </p>
        <div
          style={{
            display: "flex",
            gap: "1.5rem",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {["Estatuto Tributario", "Ley 2155/2021", "DIAN UVT 2026", "Cámara de Comercio"].map(
            (label) => (
              <span
                key={label}
                style={{
                  fontSize: "0.8125rem",
                  color: "#64748b",
                  background: "#f1f5f9",
                  padding: "0.375rem 0.75rem",
                  borderRadius: "999px",
                  border: "1px solid #e2e8f0",
                }}
              >
                {label}
              </span>
            )
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main wizard client ──────────────────────────────────────
export default function WizardClient() {
  const searchParams = useSearchParams();
  const store = useWizardStore();
  const [started, setStarted] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Prefill mode: empty by default — ?prefill=connatural activates test data for Juan Esteban
    const prefill = searchParams.get("prefill");
    if (prefill === "connatural") {
      store.setPrefillConnatural();
      setStarted(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const completedSteps = Array.from(
    { length: store.pasoActual - 1 },
    (_, i) => i + 1
  );
  const next = () => store.setPasoActual(Math.min(store.pasoActual + 1, 8));
  const back = () => store.setPasoActual(Math.max(store.pasoActual - 1, 1));

  if (!mounted) return null;

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "#f8fafc",
      }}
    >
      <WizardHeader />

      <main style={{ flex: 1 }}>
        {!started ? (
          <WizardHero
            onStart={() => {
              setStarted(true);
              store.setPasoActual(1);
            }}
          />
        ) : (
          <div
            style={{
              maxWidth: "800px",
              margin: "0 auto",
              padding: "1.5rem 1.5rem 3rem",
            }}
          >
            {/* Stepper */}
            <div
              className="ctx-card"
              style={{ marginBottom: "1.5rem", padding: "0.75rem 1.25rem" }}
            >
              <Stepper
                currentStep={store.pasoActual}
                completedSteps={completedSteps}
              />
            </div>

            {/* Step router */}
            {store.pasoActual === 1 && <Step1Solicitante onNext={next} />}
            {store.pasoActual === 2 && (
              <Step2Empresa onNext={next} onBack={back} />
            )}
            {store.pasoActual === 3 && (
              <Step3Sociedad onNext={next} onBack={back} />
            )}
            {store.pasoActual === 4 && (
              <Step4Financiera onNext={next} onBack={back} />
            )}
            {store.pasoActual === 5 && (
              <Step5Contable onNext={next} onBack={back} />
            )}
            {store.pasoActual === 6 && (
              <Step6Administrativa onNext={next} onBack={back} />
            )}
            {store.pasoActual === 7 && (
              <Step7Digital onNext={next} onBack={back} />
            )}
            {store.pasoActual === 8 && <Step8Diagnostico onBack={back} />}
          </div>
        )}
      </main>

      <WizardFooter />
      <TatyFloat />
    </div>
  );
}
