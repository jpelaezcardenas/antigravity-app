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
                  color: isActive ? "#00a878" : isCompleted ? "#00a878" : "#94a3b8",
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
                  height: "2px",
                  background: isCompleted ? "#00a878" : "#e2e8f0",
                  marginTop: "1.125rem",
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
