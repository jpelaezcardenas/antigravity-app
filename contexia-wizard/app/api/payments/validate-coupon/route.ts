import { NextRequest, NextResponse } from "next/server";
import { validateCoupon } from "@/lib/payments/coupons";
import { calculateFinalAmount } from "@/lib/payments/pricing";

export async function POST(req: NextRequest) {
  try {
    const { code } = await req.json();
    const result = validateCoupon(code || "");
    const pricing = calculateFinalAmount(result.valid ? code : null);
    return NextResponse.json({
      valid: result.valid,
      discountCop: result.discountCop,
      description: result.description,
      baseCop: pricing.baseCop,
      finalCop: pricing.finalCop,
    });
  } catch {
    return NextResponse.json({ valid: false, discountCop: 0, description: null }, { status: 400 });
  }
}
