import { NextRequest, NextResponse } from "next/server";
import { getPaymentByReference } from "@/lib/supabase/payments";

export async function GET(_req: NextRequest, ctx: { params: Promise<{ reference: string }> }) {
  const { reference } = await ctx.params;
  if (!reference) return NextResponse.json({ error: "missing reference" }, { status: 400 });
  const payment = await getPaymentByReference(reference);
  if (!payment) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({
    reference: payment.reference,
    status: payment.status,
    paymentMethod: payment.payment_method,
    wompiTransactionId: payment.wompi_transaction_id,
    finalAmountCop: payment.final_amount_cop,
    customerEmail: payment.customer_email,
  });
}
