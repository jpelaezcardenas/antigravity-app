"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useWizardStore } from "@/lib/store";
import { isFeria, getFeriaConfig } from "@/lib/feriaConfig";
import WizardHeader from "@/components/layout/WizardHeader";
import WizardFooter from "@/components/layout/WizardFooter";
import FeriaBanner from "@/components/layout/FeriaBanner";
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

// ─── Hero banner (pre-step-1) — versión NORMAL ──────────────
function WizardHeroNormal({ onStart }: { onStart: () => void }) {
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
          background: "rgba(45, 212, 191, 0.1)",
          color: "var(--ctx-teal)",
          fontWeight: 700,
          fontSize: "0.875rem",
          padding: "0.375rem 1rem",
          borderRadius: "999px",
          marginBottom: "1.5rem",
          border: "1px solid rgba(45, 212, 191, 0.2)",
        }}
      >
        🔍 Shadow Audit — Gratis &amp; Sin compromiso
      </div>
      <h1
        style={{
          fontSize: "clamp(2rem, 5vw, 2.75rem)",
          fontWeight: 800,
          color: "#ffffff",
          lineHeight: 1.2,
          margin: "0 0 1rem",
        }}
      >
        ¿Tu empresa paga más
        <br />
        <span className="gradient-text">impuestos de lo que debe?</span>
      </h1>
      <p
        style={{
          color: "var(--ctx-text-muted)",
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
              color: "var(--ctx-text-muted)",
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

      <p style={{ color: "var(--ctx-text-light)", fontSize: "0.875rem", marginTop: "1.25rem" }}>
        Sin tarjeta de crédito. Sin spam. Solo insights reales.
      </p>

      {/* Trust logos row */}
      <div
        style={{
          marginTop: "3rem",
          paddingTop: "2rem",
          borderTop: "1px solid rgba(255,255,255,0.05)",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          alignItems: "center",
        }}
      >
        <p style={{ color: "var(--ctx-text-light)", fontSize: "0.8125rem" }}>
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
                  color: "var(--ctx-text-muted)",
                  background: "rgba(255,255,255,0.03)",
                  padding: "0.375rem 1rem",
                  borderRadius: "999px",
                  border: "1px solid rgba(255,255,255,0.08)",
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

// ─── Hero banner — versión FERIA (Estud-IA personalizado) ───
function WizardHeroFeria({ onStart }: { onStart: () => void }) {
  const config = getFeriaConfig()!;

  return (
    <div
      style={{
        textAlign: "center",
        padding: "4rem 1.5rem 3rem",
        maxWidth: "800px",
        margin: "0 auto",
      }}
    >
      {/* Event badge */}
      <div
        className="feria-badge-glow"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "linear-gradient(135deg, rgba(249,115,22,0.2), rgba(168,85,247,0.2))",
          color: "#fb923c",
          fontWeight: 800,
          fontSize: "0.875rem",
          padding: "0.5rem 1.25rem",
          borderRadius: "999px",
          marginBottom: "1.5rem",
          border: "1px solid rgba(249,115,22,0.35)",
          letterSpacing: "0.025em",
        }}
      >
        {config.heroBadge}
      </div>

      {/* Main title */}
      <h1
        style={{
          fontSize: "clamp(2rem, 5vw, 3rem)",
          fontWeight: 800,
          color: "#ffffff",
          lineHeight: 1.15,
          margin: "0 0 1.25rem",
        }}
      >
        {config.heroTitle}
        <br />
        <span className="gradient-text-feria">{config.heroTitleGradient}</span>
      </h1>

      {/* Subtitle */}
      <p
        style={{
          color: "var(--ctx-text-muted)",
          fontSize: "1.0625rem",
          lineHeight: 1.75,
          margin: "0 0 2.5rem",
          maxWidth: "620px",
          marginLeft: "auto",
          marginRight: "auto",
        }}
      >
        {config.heroSubtitle}
      </p>

      {/* Proof points — feria specific */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "1.25rem",
          flexWrap: "wrap",
          marginBottom: "2.5rem",
        }}
      >
        {config.proofPoints.map((p) => (
          <div
            key={p.text}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              color: "var(--ctx-text-muted)",
              fontSize: "0.9375rem",
              background: "rgba(255,255,255,0.03)",
              padding: "0.5rem 1rem",
              borderRadius: "999px",
              border: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <span>{p.icon}</span>
            <span>{p.text}</span>
          </div>
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={onStart}
        className="ctx-btn-primary feria-cta-glow"
        style={{ fontSize: "1.125rem", padding: "1.125rem 3rem", borderRadius: "14px" }}
      >
        {config.heroCTA}
      </button>

      <p style={{ color: "var(--ctx-text-light)", fontSize: "0.875rem", marginTop: "1.25rem" }}>
        {config.heroSubCTA}
      </p>

      {/* Trust badges — feria aligned */}
      <div
        style={{
          marginTop: "3rem",
          paddingTop: "2rem",
          borderTop: "1px solid rgba(249,115,22,0.15)",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          alignItems: "center",
        }}
      >
        <p style={{ color: "var(--ctx-text-light)", fontSize: "0.8125rem" }}>
          Respaldado por el ecosistema de innovación de Medellín
        </p>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {config.trustBadges.map((label) => (
            <span
              key={label}
              style={{
                fontSize: "0.8125rem",
                color: "#fb923c",
                background: "rgba(249,115,22,0.08)",
                padding: "0.4rem 1rem",
                borderRadius: "999px",
                border: "1px solid rgba(249,115,22,0.2)",
                fontWeight: 600,
              }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Event details card */}
      <div
        style={{
          marginTop: "2.5rem",
          background: "rgba(15, 23, 42, 0.6)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(249,115,22,0.2)",
          borderRadius: "16px",
          padding: "1.25rem 1.5rem",
          display: "inline-flex",
          alignItems: "center",
          gap: "2rem",
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        <span style={{ color: "#94a3b8", fontSize: "0.875rem" }}>
          📅 {config.fecha}
        </span>
        <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>
        <span style={{ color: "#94a3b8", fontSize: "0.875rem" }}>
          📍 {config.direccion}
        </span>
        <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>
        <span style={{ color: "#94a3b8", fontSize: "0.875rem" }}>
          🕗 {config.horario}
        </span>
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

  const feriaMode = isFeria();

  useEffect(() => {
    setMounted(true);
    // Prefill mode: empty by default
    // ?prefill=connatural → datos de Juan Esteban (BARF, manufactura CIIU 1090)
    // ?prefill=lead-caliente → caso TechFlow Digital (agencia digital — lead caliente growth demo)
    const prefill = searchParams.get("prefill");
    if (prefill === "connatural") {
      store.setPrefillConnatural();
      setStarted(true);
    } else if (prefill === "lead-caliente") {
      store.setPrefillLeadCaliente();
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

  if (!mounted) return (
    <div style={{ minHeight: "100vh", background: "var(--ctx-navy)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="ctx-glass" style={{ padding: "2rem", borderRadius: "1.5rem" }}>
        <div className="animate-pulse" style={{ color: "var(--ctx-teal)" }}>Cargando Contexia...</div>
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
      {feriaMode && <FeriaBanner />}
      <WizardHeader />

      <main style={{ flex: 1, paddingTop: feriaMode ? "200px" : "160px" }}>
        {!started ? (
          feriaMode ? (
            <WizardHeroFeria
              onStart={() => {
                setStarted(true);
                store.setPasoActual(1);
              }}
            />
          ) : (
            <WizardHeroNormal
              onStart={() => {
                setStarted(true);
                store.setPasoActual(1);
              }}
            />
          )
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
