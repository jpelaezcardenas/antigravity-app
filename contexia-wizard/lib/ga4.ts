/**
 * GA4 Event Tracking — Shadow Audit Wizard
 * Sends custom events to Google Analytics 4 (G-Q03PYP6RBH)
 * Falls back silently if gtag is not loaded.
 */

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

type WizardEventName =
  | "wizard_started"
  | "wizard_step_completed"
  | "audit_executed"
  | "pdf_downloaded"
  | "email_sent"
  | "cta_clicked"
  | "whatsapp_opened"
  | "ciiu1090_banner_shown";

interface WizardEventParams {
  step?: number;
  step_name?: string;
  regimen?: "simple" | "ordinario";
  readiness_score?: number;
  riesgos_count?: number;
  ahorro_potencial?: number;
  cta_label?: string;
  ciiu?: string;
}

/**
 * Track a Shadow Audit wizard event.
 * Safe to call in any environment; no-ops if gtag is unavailable.
 */
export function trackWizardEvent(
  name: WizardEventName,
  params: WizardEventParams = {}
): void {
  if (typeof window === "undefined") return;
  if (typeof window.gtag !== "function") {
    // Stub: log in dev for debugging
    if (process.env.NODE_ENV === "development") {
      console.debug("[GA4 Stub]", name, params);
    }
    return;
  }
  window.gtag("event", name, {
    ...params,
    wizard_version: "1.0",
    send_to: "G-Q03PYP6RBH",
  });
}

// ─── Convenience wrappers ─────────────────────────────────────

export const ga4 = {
  wizardStarted: () => trackWizardEvent("wizard_started"),

  stepCompleted: (step: number, stepName: string) =>
    trackWizardEvent("wizard_step_completed", { step, step_name: stepName }),

  auditExecuted: (result: {
    regimen: "simple" | "ordinario";
    readiness_score: number;
    riesgos_count: number;
    ahorro_potencial: number;
  }) =>
    trackWizardEvent("audit_executed", {
      regimen: result.regimen,
      readiness_score: result.readiness_score,
      riesgos_count: result.riesgos_count,
      ahorro_potencial: Math.round(result.ahorro_potencial / 1_000_000), // en millones COP
    }),

  pdfDownloaded: () => trackWizardEvent("pdf_downloaded"),

  emailSent: () => trackWizardEvent("email_sent"),

  ctaClicked: (label: string) =>
    trackWizardEvent("cta_clicked", { cta_label: label }),

  whatsappOpened: () => trackWizardEvent("whatsapp_opened"),

  ciiu1090BannerShown: () => trackWizardEvent("ciiu1090_banner_shown", { ciiu: "1090" }),
};
