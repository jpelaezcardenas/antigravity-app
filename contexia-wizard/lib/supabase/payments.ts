import { supabaseAdmin } from "@/lib/supabase";
import type { WompiTransactionStatus, PaymentMethodType } from "@/lib/wompi/types";

export interface CreatePaymentInput {
  reference: string;
  leadId?: string | null;
  empresaId?: string | null;
  baseAmountCop: number;
  discountCop: number;
  finalAmountCop: number;
  amountCents: number;
  couponCode?: string | null;
  customerEmail: string;
  customerPhone?: string | null;
  customerName?: string | null;
}

export async function createPayment(input: CreatePaymentInput) {
  const { data, error } = await supabaseAdmin
    .from("payments")
    .insert({
      reference: input.reference,
      lead_id: input.leadId ?? null,
      empresa_id: input.empresaId ?? null,
      base_amount_cop: input.baseAmountCop,
      discount_cop: input.discountCop,
      final_amount_cop: input.finalAmountCop,
      amount_cents: input.amountCents,
      coupon_code: input.couponCode ?? null,
      customer_email: input.customerEmail,
      customer_phone: input.customerPhone ?? null,
      customer_name: input.customerName ?? null,
      status: "PENDING",
    })
    .select("id, reference")
    .single();
  if (error) throw error;
  return data;
}

export async function updatePaymentStatus(args: {
  reference: string;
  status: WompiTransactionStatus;
  paymentMethod?: PaymentMethodType | null;
  wompiTransactionId?: string | null;
  rawResponse?: unknown;
}) {
  const patch: Record<string, unknown> = {
    status: args.status,
    updated_at: new Date().toISOString(),
  };
  if (args.paymentMethod) patch.payment_method = args.paymentMethod;
  if (args.wompiTransactionId) patch.wompi_transaction_id = args.wompiTransactionId;
  if (args.rawResponse) patch.wompi_raw_response = args.rawResponse;
  if (args.status === "APPROVED") patch.approved_at = new Date().toISOString();

  const { data, error } = await supabaseAdmin
    .from("payments")
    .update(patch)
    .eq("reference", args.reference)
    .select("*")
    .single();
  if (error) throw error;
  return data;
}

export async function getPaymentByReference(reference: string) {
  const { data, error } = await supabaseAdmin
    .from("payments")
    .select("*")
    .eq("reference", reference)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export interface CreateEmpresaInput {
  leadId?: string | null;
  razonSocial: string;
  tipoSociedad: string;
  descripcion?: string | null;
  ciiu?: string | null;
  ciudad?: string | null;
  departamento?: string | null;
  direccion?: string | null;
  capitalTotalCop?: number | null;
  capitalSuscritoPct?: number | null;
  capitalPagadoPct?: number | null;
  accionistas?: unknown;
  representanteLegal?: unknown;
}

export async function createEmpresa(input: CreateEmpresaInput) {
  const { data, error } = await supabaseAdmin
    .from("empresas")
    .insert({
      lead_id: input.leadId ?? null,
      razon_social: input.razonSocial,
      tipo_sociedad: input.tipoSociedad,
      descripcion: input.descripcion ?? null,
      ciiu: input.ciiu ?? null,
      ciudad: input.ciudad ?? null,
      departamento: input.departamento ?? null,
      direccion: input.direccion ?? null,
      capital_total_cop: input.capitalTotalCop ?? null,
      capital_suscrito_pct: input.capitalSuscritoPct ?? null,
      capital_pagado_pct: input.capitalPagadoPct ?? null,
      accionistas: input.accionistas ?? null,
      representante_legal: input.representanteLegal ?? null,
    })
    .select("id")
    .single();
  if (error) throw error;
  return data;
}
