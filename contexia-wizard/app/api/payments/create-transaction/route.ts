import { NextRequest, NextResponse } from "next/server";
import { calculateFinalAmount } from "@/lib/payments/pricing";
import { createIntegritySignature, newReference } from "@/lib/wompi/client";
import { createEmpresa, createPayment } from "@/lib/supabase/payments";
import { supabaseAdmin } from "@/lib/supabase";

interface WizardPayload {
  contacto: { nombre: string; telefono: string; email: string };
  tipoSociedad: string;
  nombreEmpresa: string;
  descripcion: { actividad: string; ciiu?: string; direccion: string; ciudad: string; departamento: string };
  accionistas: Array<{ id: string; nombre: string; cedula: string; participacion: number }>;
  capital: { total: number; suscritoPct: number; pagadoPct: number };
  representante: { origen: "socio" | "otro"; socioId?: string; nombre?: string; cedula?: string; telefono?: string; email?: string };
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const wizard = body.wizardData as WizardPayload;
    const couponCode: string | null = body.couponCode || null;
    if (!wizard?.contacto?.email || !wizard?.contacto?.nombre || !wizard?.nombreEmpresa) {
      return NextResponse.json({ error: "Datos incompletos" }, { status: 400 });
    }

    const pricing = calculateFinalAmount(couponCode);

    // Upsert lead (reuses existing leads table)
    const { data: leadRow } = await supabaseAdmin
      .from("leads")
      .upsert(
        {
          nombre: wizard.contacto.nombre,
          email: wizard.contacto.email.toLowerCase().trim(),
          whatsapp: `+57${wizard.contacto.telefono.replace(/\D/g, "")}`,
          ciudad: wizard.descripcion.ciudad,
          status: "crear_empresa_pago",
        },
        { onConflict: "email", ignoreDuplicates: false }
      )
      .select("id")
      .single();
    const leadId = leadRow?.id ?? null;

    // Resolve representante name for storage
    const representanteLegal =
      wizard.representante.origen === "socio"
        ? {
            origen: "socio",
            nombre: wizard.accionistas.find((a) => a.id === wizard.representante.socioId)?.nombre || null,
            cedula: wizard.accionistas.find((a) => a.id === wizard.representante.socioId)?.cedula || null,
          }
        : { ...wizard.representante, origen: "otro" as const };

    const empresa = await createEmpresa({
      leadId,
      razonSocial: wizard.nombreEmpresa,
      tipoSociedad: wizard.tipoSociedad,
      descripcion: wizard.descripcion.actividad,
      ciiu: wizard.descripcion.ciiu || null,
      ciudad: wizard.descripcion.ciudad || null,
      departamento: wizard.descripcion.departamento || null,
      direccion: wizard.descripcion.direccion || null,
      capitalTotalCop: wizard.capital.total,
      capitalSuscritoPct: wizard.capital.suscritoPct,
      capitalPagadoPct: wizard.capital.pagadoPct,
      accionistas: wizard.accionistas,
      representanteLegal,
    });

    const reference = newReference("CXIA-CE");
    await createPayment({
      reference,
      leadId,
      empresaId: empresa.id,
      baseAmountCop: pricing.baseCop,
      discountCop: pricing.discountCop,
      finalAmountCop: pricing.finalCop,
      amountCents: pricing.amountInCents,
      couponCode: pricing.couponCode,
      customerEmail: wizard.contacto.email,
      customerPhone: `+57${wizard.contacto.telefono.replace(/\D/g, "")}`,
      customerName: wizard.contacto.nombre,
    });

    const signature = createIntegritySignature(reference, pricing.amountInCents, "COP");

    return NextResponse.json({
      reference,
      signature,
      amountInCents: pricing.amountInCents,
      currency: "COP",
      publicKey: process.env.NEXT_PUBLIC_WOMPI_PUBLIC_KEY,
      pricing: {
        baseCop: pricing.baseCop,
        discountCop: pricing.discountCop,
        finalCop: pricing.finalCop,
        couponCode: pricing.couponCode,
        couponDescription: pricing.couponDescription,
      },
    });
  } catch (err) {
    console.error("create-transaction error:", err);
    return NextResponse.json({ error: "Error creando transacción" }, { status: 500 });
  }
}
