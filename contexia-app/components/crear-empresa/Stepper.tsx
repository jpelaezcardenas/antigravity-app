"use client";

import type { WizardStep } from "@/lib/types/crearEmpresa";
import { WIZARD_STEPS_LABELS } from "@/lib/types/crearEmpresa";

interface StepperProps {
  current: WizardStep;
  total?: number;
}

export function Stepper({ current, total = 8 }: StepperProps) {
  const pct = ((current - 1) / (total - 1)) * 100;

  return (
    <div className="w-full">
      {/* Mobile: minimal "Paso N de 8" + bar */}
      <div className="md:hidden flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span
            className="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Paso {current} de {total}
          </span>
          <span
            className="text-[11px] font-bold uppercase tracking-widest text-[#2DD4BF]"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            {WIZARD_STEPS_LABELS[current].short}
          </span>
        </div>
        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#2DD4BF] to-[#8B5CF6] transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Desktop: full stepper with dots and labels */}
      <div className="hidden md:flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span
            className="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Crear tu empresa
          </span>
          <span
            className="text-[11px] font-bold uppercase tracking-widest text-[#2DD4BF]"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Paso {current} de {total}
          </span>
        </div>

        <div className="relative h-1 w-full bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#2DD4BF] to-[#8B5CF6] transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="flex items-start justify-between gap-2 mt-1">
          {(Object.keys(WIZARD_STEPS_LABELS) as unknown as WizardStep[]).map((s) => {
            const stepNum = Number(s) as WizardStep;
            const isActive = stepNum === current;
            const isPast = stepNum < current;
            return (
              <div
                key={stepNum}
                className={`flex-1 flex flex-col items-center gap-1 text-center transition-colors ${
                  isActive
                    ? "text-[#2DD4BF]"
                    : isPast
                      ? "text-on-surface"
                      : "text-on-surface-variant/50"
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full transition-all ${
                    isActive
                      ? "bg-[#2DD4BF] shadow-[0_0_8px_rgba(45,212,191,0.8)] scale-150"
                      : isPast
                        ? "bg-[#2DD4BF]"
                        : "bg-white/20"
                  }`}
                />
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider leading-tight ${
                    isActive ? "" : "opacity-70"
                  }`}
                  style={{ fontFamily: "Rajdhani, sans-serif" }}
                >
                  {WIZARD_STEPS_LABELS[stepNum].short}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
