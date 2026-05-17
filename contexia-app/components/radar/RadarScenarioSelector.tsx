"use client";

import type { Scenario } from "@/lib/types/contexia";

interface RadarScenarioSelectorProps {
  value: Scenario;
  onChange: (next: Scenario) => void;
}

const OPTIONS: { value: Scenario; label: string }[] = [
  { value: "pesimista", label: "Escenario Pesimista" },
  { value: "base", label: "Base" },
  { value: "optimista", label: "Optimista" },
];

export function RadarScenarioSelector({
  value,
  onChange,
}: RadarScenarioSelectorProps) {
  return (
    <div
      role="tablist"
      aria-label="Seleccionar escenario"
      className="flex gap-2 overflow-x-auto no-scrollbar py-1"
    >
      {OPTIONS.map((opt) => {
        const isActive = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(opt.value)}
            className={`h-[36px] px-4 rounded-full font-label-caps text-label-caps whitespace-nowrap transition-all active:scale-95 ${
              isActive
                ? "bg-primary text-on-primary shadow-[0_0_15px_rgba(45,212,191,0.3)]"
                : "border border-outline-variant text-on-surface-variant hover:bg-surface-variant/20"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
