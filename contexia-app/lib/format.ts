/**
 * Formato de moneda colombiana sin decimales, separador de miles con punto.
 * 42850000 → "$42.850.000"
 */
export function formatCop(value: number): string {
  return `$${value.toLocaleString("es-CO")}`;
}
