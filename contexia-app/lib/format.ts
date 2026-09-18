/**
 * Formato de moneda colombiana sin decimales, separador de miles con punto.
 * 42850000 → "$42.850.000"
 */
export function formatCop(value: number): string {
  return `$${value.toLocaleString("es-CO")}`;
}

/**
 * "Actualizado hace X" style relative time from an ISO timestamp, in Spanish.
 * Only covers the ranges the UI actually needs (minutes/hours/days) — no
 * external date library, matching contexia-app's no-new-dependency rule.
 */
export function formatRelativeTime(isoTimestamp: string, now: Date = new Date()): string {
  const then = new Date(isoTimestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffMinutes = Math.max(0, Math.round(diffMs / 60000));

  if (diffMinutes < 1) return "hace un momento";
  if (diffMinutes < 60) return `hace ${diffMinutes} min`;

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `hace ${diffHours} ${diffHours === 1 ? "hora" : "horas"}`;

  const diffDays = Math.round(diffHours / 24);
  return `hace ${diffDays} ${diffDays === 1 ? "día" : "días"}`;
}

const SHORT_MONTHS_ES = [
  "ene", "feb", "mar", "abr", "may", "jun",
  "jul", "ago", "sep", "oct", "nov", "dic",
];

/** "13 oct" style short date from an ISO date string, for the Próximos Hitos
 * tiles (a real DIAN deadline date, deliberately shown without a year or amount). */
export function formatShortDate(isoDate: string): string {
  const [, month, day] = isoDate.split("-");
  return `${parseInt(day, 10)} ${SHORT_MONTHS_ES[parseInt(month, 10) - 1]}`;
}
