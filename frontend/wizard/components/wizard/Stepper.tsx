"use client";
import { Check } from "lucide-react";

const STEP_LABELS = [
  "Tú",
  "Empresa",
  "Socios",
  "Financiero",
  "Contable",
  "Equipo",
  "Digital",
  "Diagnóstico",
];

interface StepperProps {
  currentStep: number; // 1-8
  completedSteps: number[];
}

export default function Stepper({ currentStep, completedSteps }: StepperProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        gap: 0,
        padding: "1.25rem 0",
        overflowX: "auto",
      }}
    >
      {STEP_LABELS.map((label, i) => {
        const step = i + 1;
        const isActive = step === currentStep;
        const isCompleted = completedSteps.includes(step);

        return (
          <div
            key={step}
            style={{ display: "flex", alignItems: "flex-start", gap: 0, flex: step < 8 ? 1 : "none" }}
          >
            {/* Circle + label */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.375rem", minWidth: "60px" }}>
              <div
                className={`ctx-step-circle ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}
              >
                {isCompleted ? <Check size={14} strokeWidth={2.5} /> : step}
              </div>
              <span
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "var(--ctx-teal)" : isCompleted ? "var(--ctx-teal)" : "#64748b",
                  textAlign: "center",
                  whiteSpace: "nowrap",
                }}
              >
                {label}
              </span>
            </div>

            {/* Connector line */}
            {step < 8 && (
              <div
                style={{
                  flex: 1,
                  height: "1.5px",
                  background: isCompleted ? "var(--ctx-teal)" : "rgba(255,255,255,0.05)",
                  marginTop: "1.25rem",
                  transition: "background 0.3s",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
