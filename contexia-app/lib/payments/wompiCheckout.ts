"use client";

/**
 * Client-side Wompi widget loader. Used only in the Crear Empresa wizard's
 * payment step — this is the wizard's single concession to the "no fetch"
 * rule in CLAUDE.md, justified because the wizard is a real lead-intake form,
 * not part of the mock dashboard demo.
 */

const WIDGET_URL = "https://checkout.wompi.co/widget.js";

interface OpenArgs {
  publicKey: string;
  reference: string;
  signature: string;
  amountInCents: number;
  currency?: string;
  customerEmail: string;
  customerName?: string;
  customerPhone?: string;
  redirectUrl: string;
}

declare global {
  interface Window {
    WidgetCheckout?: new (config: Record<string, unknown>) => {
      open: (cb: (result: unknown) => void) => void;
    };
  }
}

let loading: Promise<void> | null = null;

function loadScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject(new Error("no window"));
  if (window.WidgetCheckout) return Promise.resolve();
  if (loading) return loading;
  loading = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = WIDGET_URL;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("No se pudo cargar Wompi"));
    document.head.appendChild(s);
  });
  return loading;
}

export async function openWompiCheckout(args: OpenArgs): Promise<void> {
  await loadScript();
  if (!window.WidgetCheckout) throw new Error("WidgetCheckout no disponible");
  const checkout = new window.WidgetCheckout({
    currency: args.currency || "COP",
    amountInCents: args.amountInCents,
    reference: args.reference,
    publicKey: args.publicKey,
    signature: { integrity: args.signature },
    redirectUrl: args.redirectUrl,
    customerData: {
      email: args.customerEmail,
      fullName: args.customerName,
      phoneNumber: args.customerPhone,
      phoneNumberPrefix: "+57",
    },
  });
  checkout.open(() => {
    /* Wompi handles the redirect to redirectUrl on completion */
  });
}

const API_BASE = "/wizard/api/payments";

export interface CreateTxResponse {
  reference: string;
  signature: string;
  amountInCents: number;
  currency: string;
  publicKey: string;
  pricing: {
    baseCop: number;
    discountCop: number;
    finalCop: number;
    couponCode: string | null;
    couponDescription: string | null;
  };
}

export async function createTransaction(payload: { wizardData: unknown; couponCode?: string | null }): Promise<CreateTxResponse> {
  const res = await fetch(`${API_BASE}/create-transaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface CouponResponse {
  valid: boolean;
  discountCop: number;
  description: string | null;
  baseCop: number;
  finalCop: number;
}

export async function validateCoupon(code: string): Promise<CouponResponse> {
  const res = await fetch(`${API_BASE}/validate-coupon`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) return { valid: false, discountCop: 0, description: null, baseCop: 399_000, finalCop: 399_000 };
  return res.json();
}
