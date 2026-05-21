import { NextRequest, NextResponse } from "next/server";
import { verifyWebhookSignature } from "@/lib/wompi/client";
import type { WompiWebhookEvent } from "@/lib/wompi/types";
import { getPaymentByReference, updatePaymentStatus } from "@/lib/supabase/payments";
import { supabaseAdmin } from "@/lib/supabase";
import { sendPaymentConfirmation } from "@/lib/email/sendPaymentConfirmation";

export async function POST(req: NextRequest) {
  let event: WompiWebhookEvent;
  try {
    event = (await req.json()) as WompiWebhookEvent;
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  if (!verifyWebhookSignature(event)) {
    console.error("[wompi webhook] invalid signature");
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  const tx = event.data?.transaction;
  if (!tx?.reference) {
    return NextResponse.json({ error: "missing transaction" }, { status: 400 });
  }

  try {
    const existing = await getPaymentByReference(tx.reference);
    if (!existing) {
      console.warn(`[wompi webhook] unknown reference ${tx.reference}`);
      return NextResponse.json({ ok: true });
    }
    const alreadyApproved = existing.status === "APPROVED";
    const updated = await updatePaymentStatus({
      reference: tx.reference,
      status: tx.status,
      paymentMethod: tx.payment_method_type,
      wompiTransactionId: tx.id,
      rawResponse: tx,
    });

    // Idempotency: only fire emails on the transition to APPROVED
    if (tx.status === "APPROVED" && !alreadyApproved) {
      const empresa = updated.empresa_id
        ? (await supabaseAdmin.from("empresas").select("*").eq("id", updated.empresa_id).maybeSingle()).data
        : null;
      await sendPaymentConfirmation({
        client: {
          customerName: updated.customer_name || "",
          customerEmail: updated.customer_email || "",
          razonSocial: empresa?.razon_social || "tu empresa",
          reference: updated.reference,
          finalAmountCop: updated.final_amount_cop,
          paymentMethod: tx.payment_method_type || "—",
        },
        taty: {
          customerName: updated.customer_name || "",
          customerEmail: updated.customer_email || "",
          customerPhone: updated.customer_phone || "",
          razonSocial: empresa?.razon_social || "—",
          tipoSociedad: empresa?.tipo_sociedad || "—",
          ciudad: empresa?.ciudad ?? null,
          reference: updated.reference,
          baseAmountCop: updated.base_amount_cop,
          discountCop: updated.discount_cop,
          finalAmountCop: updated.final_amount_cop,
          couponCode: updated.coupon_code,
          paymentMethod: tx.payment_method_type || "—",
          wompiTransactionId: tx.id,
          accionistas: empresa?.accionistas ?? null,
          capital: empresa
            ? { total: empresa.capital_total_cop, suscritoPct: empresa.capital_suscrito_pct, pagadoPct: empresa.capital_pagado_pct }
            : null,
          representanteNombre: (empresa?.representante_legal as { nombre?: string } | null)?.nombre ?? null,
          descripcion: empresa?.descripcion ?? null,
          ciiu: empresa?.ciiu ?? null,
        },
      });
    }
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[wompi webhook] processing error:", err);
    return NextResponse.json({ error: "processing failed" }, { status: 500 });
  }
}
