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
            background: "#e8f7f3",
            color: "#00a878",
            fontSize: "0.8125rem",
            fontWeight: 700,
            padding: "0.375rem 0.75rem",
            borderRadius: "999px",
            marginBottom: "0.75rem",
          }}
        >
          <span>Paso {step} de 8</span>
        </div>
        <h2
          style={{
            fontSize: "1.625rem",
            fontWeight: 700,
            color: "#0a2540",
            margin: "0 0 0.375rem",
          }}
        >
          {headline}
        </h2>
        {subheadline && (
          <p style={{ color: "#64748b", fontSize: "0.9375rem", margin: 0 }}>
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
        }}
      >
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="ctx-btn-outline"
            style={{ gap: "0.375rem" }}
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
