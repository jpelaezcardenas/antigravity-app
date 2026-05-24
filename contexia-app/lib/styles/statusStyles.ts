/**
 * Status styles mapping
 */

export const SEVERITY_ICON_STYLES: Record<string, string> = {
  error: "text-status-error",
  warning: "text-status-warning",
  info: "text-status-info",
  success: "text-status-success",
};

export const SEVERITY_BG_STYLES: Record<string, string> = {
  error: "bg-status-error/10",
  warning: "bg-status-warning/10",
  info: "bg-status-info/10",
  success: "bg-status-success/10",
};

export const SEVERITY_TEXT_STYLES: Record<string, string> = {
  error: "text-status-error",
  warning: "text-status-warning",
  info: "text-status-info",
  success: "text-status-success",
};

export const STATUS_COLOR: Record<string, string> = {
  success: "text-teal-400",
  warning: "text-amber-400",
  danger: "text-red-400",
  error: "text-red-400",
  info: "text-blue-400",
  neutral: "text-slate-400",
};

export const STATUS_BADGE: Record<string, string> = {
  success: "bg-teal-400/10 text-teal-400 border-teal-400/20",
  warning: "bg-amber-400/10 text-amber-400 border-amber-400/20",
  danger: "bg-red-400/10 text-red-400 border-red-400/20",
  error: "bg-red-400/10 text-red-400 border-red-400/20",
  info: "bg-blue-400/10 text-blue-400 border-blue-400/20",
  neutral: "bg-slate-400/10 text-slate-400 border-slate-400/20",
};

export const STATUS_HEALTH_BADGE: Record<string, string> = {
  excelente: "bg-teal-400/10 text-teal-400 border-teal-400/20",
  saludable: "bg-teal-400/10 text-teal-400 border-teal-400/20",
  estable: "bg-blue-400/10 text-blue-400 border-blue-400/20",
  alerta: "bg-amber-400/10 text-amber-400 border-amber-400/20",
  critico: "bg-red-400/10 text-red-400 border-red-400/20",
};

export const STATUS_BADGE_LABEL: Record<string, string> = {
  excelente: "Excelente",
  saludable: "Saludable",
  estable: "Estable",
  alerta: "Alerta",
  critico: "Crítico",
};

export const FLOW_COLOR_CONFIG: Record<string, string> = {
  inflow: "text-teal-400",
  outflow: "text-red-400",
  neutral: "text-slate-400",
};

export const DIRECTION_COLOR: Record<string, string> = {
  in: "text-teal-400",
  out: "text-red-400",
  neutral: "text-slate-400",
};

export const DIRECTION_ICON: Record<string, string> = {
  in: "M5 10l7-7m0 0l7 7m-7-7v18", // Arrow Up
  out: "M19 14l-7 7m0 0l-7-7m7 7V3", // Arrow Down
  neutral: "M5 12h14", // Minus
};
