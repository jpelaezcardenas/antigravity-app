/**
 * Estilos centralizados para status, severidad y variantes
 * Consolidado de múltiples componentes para evitar duplicación
 */

import type { StatusLevel, AlertSeverity, RiskLevel, ProgressVariant } from "@/lib/types/contexia";

// === Status Colors (Health States) ===
export const STATUS_COLOR: Record<StatusLevel, string> = {
  sana: "bg-status-success/10 text-status-success border-status-success/30",
  vigilancia: "bg-status-warning/10 text-status-warning border-status-warning/30",
  alerta: "bg-status-critical/10 text-status-critical border-status-critical/30",
};

// Para mostrar el estado como texto simple
export const STATUS_BADGE: Record<StatusLevel, string> = {
  sana: "Bien",
  vigilancia: "Ojo",
  alerta: "Alerta",
};

// Para FinancialHealthStatusGrid - styling detallado
export const STATUS_HEALTH_BADGE: Record<StatusLevel, { bg: string; text: string }> = {
  sana: {
    bg: "bg-status-success/10",
    text: "text-status-success border-status-success/20",
  },
  vigilancia: {
    bg: "bg-status-warning/10",
    text: "text-status-warning border-status-warning/20",
  },
  alerta: {
    bg: "bg-status-critical/10",
    text: "text-status-critical border-status-critical/20",
  },
};

export const STATUS_BADGE_LABEL: Record<StatusLevel, string> = {
  sana: "BIEN",
  vigilancia: "OJO",
  alerta: "ALERTA",
};

export const STATUS_DOT_COLOR: Record<StatusLevel, string> = {
  sana: "bg-status-success",
  vigilancia: "bg-status-warning",
  alerta: "bg-status-critical",
};

// === Severity Styles (Alerts) ===
export const SEVERITY_STYLES: Record<AlertSeverity, string> = {
  warning:
    "bg-status-warning/10 text-status-warning border-status-warning/30 hover:bg-status-warning/20 transition-colors",
  critical:
    "bg-status-critical/10 text-status-critical border-status-critical/30 hover:bg-status-critical/20 transition-colors",
};

// Estructura detallada para ActiveAlerts
export const SEVERITY_ICON_STYLES: Record<
  AlertSeverity,
  { border: string; iconBg: string; iconColor: string }
> = {
  warning: {
    border: "border-status-warning/20",
    iconBg: "bg-status-warning/10",
    iconColor: "text-status-warning",
  },
  critical: {
    border: "border-status-critical/20",
    iconBg: "bg-status-critical/10",
    iconColor: "text-status-critical",
  },
};

export const SEVERITY_ICON_COLOR: Record<AlertSeverity, string> = {
  warning: "text-status-warning",
  critical: "text-status-critical",
};

// === Risk Level Colors (Fiscal) ===
export const RISK_COLOR: Record<RiskLevel, string> = {
  bajo: "bg-status-success/10 text-status-success border-status-success/30",
  medio: "bg-status-warning/10 text-status-warning border-status-warning/30",
  alto: "bg-status-critical/10 text-status-critical border-status-critical/30",
};

export const RISK_LABEL: Record<RiskLevel, string> = {
  bajo: "Tranqui",
  medio: "Ojo",
  alto: "Alerta",
};

// === Progress Bar Variants ===
export const PROGRESS_VARIANT_COLOR: Record<ProgressVariant, string> = {
  primary: "bg-primary",
  success: "bg-status-success",
  warning: "bg-status-warning",
  critical: "bg-status-critical",
};

export const PROGRESS_VARIANT_TEXT: Record<ProgressVariant, string> = {
  primary: "text-primary",
  success: "text-status-success",
  warning: "text-status-warning",
  critical: "text-status-critical",
};

export const PROGRESS_VARIANT_BG: Record<ProgressVariant, string> = {
  primary: "bg-primary/20",
  success: "bg-status-success/20",
  warning: "bg-status-warning/20",
  critical: "bg-status-critical/20",
};

// === Direction Icons (Movements) ===
export const DIRECTION_ICON: Record<"outflow" | "inflow", { icon: string; color: string }> = {
  outflow: {
    icon: "south_east",
    color: "text-status-critical",
  },
  inflow: {
    icon: "north_east",
    color: "text-status-success",
  },
};

export const DIRECTION_COLOR: Record<"outflow" | "inflow", string> = {
  outflow: "text-status-critical",
  inflow: "text-status-success",
};

// === Projection Tones (Cash Charts) ===
export const TONE_COLOR: Record<"warning" | "base" | "positive", string> = {
  warning: "text-status-warning",
  base: "text-on-surface-variant",
  positive: "text-status-success",
};

export const TONE_GLOW: Record<"warning" | "base" | "positive", string> = {
  warning: "shadow-[0_0_20px_rgba(250,204,21,0.25)]",
  base: "shadow-[0_0_20px_rgba(88,80,143,0.1)]",
  positive: "shadow-[0_0_20px_rgba(34,197,94,0.25)]",
};

// === Color Config for Flow Composition (by color key) ===
export const FLOW_COLOR_CONFIG: Record<string, { bg: string; shadow: string; dot: string }> = {
  "text-status-success": {
    bg: "bg-status-success",
    shadow: "shadow-[0_0_10px_rgba(34,197,94,0.4)]",
    dot: "shadow-[0_0_8px_rgba(34,197,94,0.6)]",
  },
  "text-primary": {
    bg: "bg-primary",
    shadow: "shadow-[0_0_10px_rgba(45,212,191,0.3)]",
    dot: "shadow-[0_0_8px_rgba(45,212,191,0.5)]",
  },
  "text-status-warning": {
    bg: "bg-status-warning",
    shadow: "shadow-[0_0_10px_rgba(250,204,21,0.4)]",
    dot: "shadow-[0_0_8px_rgba(250,204,21,0.6)]",
  },
};
