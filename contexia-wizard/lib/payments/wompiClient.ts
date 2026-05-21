"use client";

import { WOMPI_WIDGET_URL } from "@/lib/wompi/client";

interface OpenCheckoutArgs {
  publicKey: string;
  reference: string;
  signature: string;
  amountInCents: number;
  currency?: string;
  customerEmail: string;
  customerData?: { fullName?: string; phoneNumber?: string };
  redirectUrl: string;
}

declare global {
  interface Window {
    WidgetCheckout?: new (config: Record<string, unknown>) => { open: (cb: (result: unknown) => void) => void };
  }
}

let scriptLoading: Promise<void> | null = null;

function loadWompiScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject(new Error("no window"));
  if (window.WidgetCheckout) return Promise.resolve();
  if (scriptLoading) return scriptLoading;
  scriptLoading = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = WOMPI_WIDGET_URL;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("No se pudo cargar el widget de Wompi"));
    document.head.appendChild(s);
  });
  return scriptLoading;
}

export async function openWompiCheckout(args: OpenCheckoutArgs): Promise<void> {
  await loadWompiScript();
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
      fullName: args.customerData?.fullName,
      phoneNumber: args.customerData?.phoneNumber,
      phoneNumberPrefix: "+57",
    },
  });
  checkout.open(() => {
    // Wompi will redirect to redirectUrl; nothing to do here.
  });
}
