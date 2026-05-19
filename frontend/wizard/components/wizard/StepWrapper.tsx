"use client";
import { ReactNode } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";

interface StepWrapperProps {
  step: number;
  headline: string;
  subheadline?: string;
  children: ReactNode;
  onNext?: () => void;
  onBack?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  isLastStep?: boolean;
}

export default function StepWrapper({
  step,
  headline,
  subheadline,
  children,
  onNext,
  onBack,
  nextLabel = "Siguiente →",
  nextDisabled = false,
  isLastStep = false,
}: StepWrapperProps) {
  return (
    <div className="animate-fadeInUp">
      {/* Step header */}
      <div style={{ marginBottom: "2rem" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            background: "rgba(45, 212, 191, 0.1)",
            color: "var(--ctx-teal)",
            fontSize: "0.8125rem",
            fontWeight: 700,
            padding: "0.375rem 0.875rem",
            borderRadius: "999px",
            marginBottom: "0.75rem",
            border: "1px solid rgba(45, 212, 191, 0.2)",
          }}
        >
          <span>Paso {step} de 8</span>
        </div>
        <h2
          className="font-orbitron"
          style={{
            fontSize: "1.625rem",
            fontWeight: 800,
            color: "white",
            margin: "0 0 0.5rem",
            letterSpacing: "0.02em",
          }}
        >
          {headline}
        </h2>
        {subheadline && (
          <p style={{ color: "var(--ctx-text-muted)", fontSize: "0.9375rem", margin: 0 }}>
            {subheadline}
          </p>
        )}
      </div>

      {/* Content */}
      <div className="ctx-card ctx-card-lg" style={{ marginBottom: "1.5rem" }}>
        {children}
      </div>

      {/* Navigation */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "1rem",
          marginTop: "2.5rem",
          paddingBottom: "1.5rem",
        }}
      >
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="ctx-btn-secondary"
            style={{ gap: "0.375rem", padding: "0.75rem 1.5rem" }}
          >
            <ArrowLeft size={16} />
            Atrás
          </button>
        ) : (
          <div />
        )}

        {onNext && (
          <button
            type="button"
            onClick={onNext}
            disabled={nextDisabled}
            className="ctx-btn-primary"
            style={{ gap: "0.375rem", minWidth: "160px" }}
          >
            {nextLabel}
            {!isLastStep && <ArrowRight size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}
