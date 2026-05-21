export interface CouponDefinition {
  discountCop: number;
  description: string;
}

/**
 * Hardcoded coupons (Phase 1). Edit here to add or change campaigns.
 * Phase 2: move to Supabase table with expiry + usage limits.
 */
export const COUPONS: Record<string, CouponDefinition> = {
  LANZAMIENTO50: { discountCop: 50_000, description: "Lanzamiento −$50.000" },
  FRIENDS: { discountCop: 100_000, description: "Amigos de Taty −$100.000" },
  TARJETA20: { discountCop: 80_000, description: "Pago con tarjeta −20%" },
  TATY10: { discountCop: 40_000, description: "Cupón Taty −$40.000" },
};

export interface CouponResult {
  valid: boolean;
  discountCop: number;
  description: string | null;
}

export function validateCoupon(code: string): CouponResult {
  const key = (code || "").trim().toUpperCase();
  if (!key) return { valid: false, discountCop: 0, description: null };
  const found = COUPONS[key];
  if (!found) return { valid: false, discountCop: 0, description: null };
  return { valid: true, discountCop: found.discountCop, description: found.description };
}
