import { validateCoupon } from "./coupons";

export const PRICE_CREAR_EMPRESA_COP = 399_000;
export const MIN_FINAL_AMOUNT_COP = 1_000;

export interface FinalAmount {
  baseCop: number;
  discountCop: number;
  finalCop: number;
  amountInCents: number;
  couponCode: string | null;
  couponDescription: string | null;
}

export function calculateFinalAmount(couponCode?: string | null): FinalAmount {
  const base = PRICE_CREAR_EMPRESA_COP;
  const result = couponCode ? validateCoupon(couponCode) : { valid: false, discountCop: 0, description: null };
  const discount = result.valid ? Math.min(result.discountCop, base - MIN_FINAL_AMOUNT_COP) : 0;
  const finalCop = Math.max(base - discount, MIN_FINAL_AMOUNT_COP);
  return {
    baseCop: base,
    discountCop: discount,
    finalCop,
    amountInCents: finalCop * 100,
    couponCode: result.valid ? (couponCode ?? null) : null,
    couponDescription: result.valid ? result.description : null,
  };
}
