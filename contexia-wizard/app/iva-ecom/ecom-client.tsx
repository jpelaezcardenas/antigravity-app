"use client";
import { useState, useEffect } from "react";
import { useEcomStore } from "@/lib/ecomStore";
import WizardHeader from "@/components/layout/WizardHeader";
import WizardFooter from "@/components/layout/WizardFooter";
import TatyFloat from "@/components/layout/TatyFloat";
import Step1Numeros from "@/components/wizard-ecom/Step1Numeros";
import Step2Formalizacion from "@/components/wizard-ecom/Step2Formalizacion";
import Step3Resultado from "@/components/wizard-ecom/Step3Resultado";

/**
 * Client for the 3-step express IVA diagnostic
 * (wizard-iva-ecom-express-diagnostic). A separate router from
 * app/wizard-client.tsx (the existing 8-step flow) — see
 * lib/ecomStore.ts for why the store is separate too.
 */
export default function EcomWizardClient() {
  const store = useEcomStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const next = () =>
    store.setPasoActual((Math.min(store.pasoActual + 1, 3) as 1 | 2 | 3));
  const back = () =>
    store.setPasoActual((Math.max(store.pasoActual - 1, 1) as 1 | 2 | 3));

  if (!mounted)
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "var(--ctx-navy)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div className="ctx-glass" style={{ padding: "2rem", borderRadius: "1.5rem" }}>
          <div className="animate-pulse" style={{ color: "var(--ctx-teal)" }}>
            Cargando diagnóstico exprés...
          </div>
        </div>
      </div>
    );

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "#020617",
      }}
    >
      <WizardHeader />

      <main style={{ flex: 1, paddingTop: "200px" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto", padding: "1.5rem 1.5rem 3rem" }}>
          {store.pasoActual === 1 && (
            <div style={{ textAlign: "center", marginBottom: "2rem" }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  background: "rgba(45, 212, 191, 0.1)",
                  color: "var(--ctx-teal)",
                  fontWeight: 700,
                  fontSize: "0.8125rem",
                  padding: "0.375rem 1rem",
                  borderRadius: "999px",
                  marginBottom: "1rem",
                  border: "1px solid rgba(45, 212, 191, 0.2)",
                }}
              >
                🔍 Diagnóstico Exprés de IVA
              </div>
              <h1
                className="font-orbitron"
                style={{
                  fontSize: "clamp(1.5rem, 4vw, 2rem)",
                  fontWeight: 800,
                  color: "#ffffff",
                  lineHeight: 1.25,
                  margin: "0 0 0.75rem",
                }}
              >
                ¿Cuánto IVA podrías estar{" "}
                <span className="gradient-text">dejando sobre la mesa?</span>
              </h1>
              <p
                style={{
                  color: "var(--ctx-text-muted)",
                  fontSize: "0.9375rem",
                  maxWidth: "480px",
                  margin: "0 auto",
                }}
              >
                Responde 3 preguntas rápidas sobre tu negocio digital y en 30 segundos te mostramos
                un estimado, sin compromiso.
              </p>
            </div>
          )}
          {store.pasoActual === 1 && <Step1Numeros onNext={next} />}
          {store.pasoActual === 2 && (
            <Step2Formalizacion onNext={next} onBack={back} />
          )}
          {store.pasoActual === 3 && <Step3Resultado onBack={back} />}
        </div>
      </main>

      <WizardFooter />
      <TatyFloat />
    </div>
  );
}
