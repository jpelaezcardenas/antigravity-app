import type { ProgressVariant } from "@/lib/types/contexia";

interface ProgressBarProps {
  /** Porcentaje 0-100. Se clampea automáticamente. */
  percent: number;
  /** Color del fill. Default: "primary" (teal Contexia). */
  variant?: ProgressVariant;
  /** Tamaño del track. Default: "md" (h-2). */
  size?: "sm" | "md";
  /** Override del track. Default: "bg-surface-container-high". */
  trackClassName?: string;
}

const VARIANT_FILL: Record<ProgressVariant, string> = {
  primary:
    "bg-primary-container shadow-[0_0_10px_rgba(45,212,191,0.5)]",
  success:
    "bg-status-success shadow-[0_0_10px_rgba(45,212,191,0.5)]",
  warning:
    "bg-status-warning shadow-[0_0_10px_rgba(245,158,11,0.5)]",
  critical:
    "bg-status-critical shadow-[0_0_10px_rgba(239,68,68,0.5)]",
};

const SIZE_CLASS: Record<"sm" | "md", string> = {
  sm: "h-1.5",
  md: "h-2",
};

export function ProgressBar({
  percent,
  variant = "primary",
  size = "md",
  trackClassName = "bg-surface-container-high",
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div
      className={`w-full ${SIZE_CLASS[size]} ${trackClassName} rounded-full overflow-hidden`}
    >
      <div
        className={`h-full rounded-full transition-all duration-300 ${VARIANT_FILL[variant]}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

/**
 * Mapea un porcentaje de "uso vs límite" a variant.
 * Entre más alto, peor (ej. UVT consumido, ratio de retiro).
 * <70 → primary, 70-85 → warning, >=85 → critical.
 */
export function variantFromUsage(percent: number): ProgressVariant {
  if (percent >= 85) return "critical";
  if (percent >= 70) return "warning";
  return "primary";
}

/**
 * Mapea un porcentaje de "avance hacia meta" a variant.
 * Entre más alto, mejor (ej. reservado/meta, ahorro acumulado).
 * <50 → critical, 50-80 → warning, >=80 → primary.
 */
export function variantFromGoal(percent: number): ProgressVariant {
  if (percent < 50) return "critical";
  if (percent < 80) return "warning";
  return "primary";
}

/** Color de texto que matchea cada variant del bar. */
export const VARIANT_TEXT_COLOR: Record<ProgressVariant, string> = {
  primary: "text-primary-container",
  success: "text-status-success",
  warning: "text-status-warning",
  critical: "text-status-critical",
};
