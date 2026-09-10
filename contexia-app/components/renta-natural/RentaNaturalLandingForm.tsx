"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { isValidCapturePhone } from "@/lib/utils/phoneValidation";
import { submitSocialCapture } from "@/lib/social-capture-api";

type SubmitState = "idle" | "submitting" | "done" | "error";

/**
 * Public lead-capture form for the `/renta-natural` landing page
 * (b2c-social-lead-capture, Task 4). Implements the Dapta Forms
 * partial-capture pattern (design.md Goals): a partial write fires the
 * moment the phone number becomes valid, before the visitor finishes or
 * submits the rest of the form, so an abandoned form still becomes a real
 * lead that Taty can contact.
 */
export function RentaNaturalLandingForm() {
  const searchParams = useSearchParams();
  const source = searchParams.get("source") || undefined;

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [partialCaptured, setPartialCaptured] = useState(false);
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | undefined>();

  const handlePhoneChange = (value: string) => {
    setPhone(value);

    // Partial capture: fire once, the first time the number becomes valid.
    // A later edit to an already-valid number does not re-fire — the
    // backend's phone throttle would just no-op it anyway, but this avoids
    // spamming the endpoint on every keystroke.
    if (!partialCaptured && isValidCapturePhone(value)) {
      setPartialCaptured(true);
      submitSocialCapture({ whatsappPhone: value, source }).catch(() => {
        // Partial capture is best-effort from the visitor's point of view —
        // never block typing or show an error for a background call. The
        // full submission below is the one that surfaces failures.
      });
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!isValidCapturePhone(phone)) {
      setErrorMsg("Ingresa un número de WhatsApp válido.");
      return;
    }

    setSubmitState("submitting");
    setErrorMsg(undefined);
    try {
      await submitSocialCapture({
        whatsappPhone: phone,
        fullName: fullName.trim() || undefined,
        source,
      });
      setSubmitState("done");
    } catch (err) {
      setSubmitState("error");
      setErrorMsg(
        err instanceof Error ? err.message : "No se pudo enviar el formulario."
      );
    }
  };

  if (submitState === "done") {
    return (
      <div
        className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center"
        role="status"
      >
        <p className="text-lg font-bold text-white">¡Listo, {fullName || "gracias"}!</p>
        <p className="mt-2 text-sm text-white/70">
          Taty, la asistente de Contexia, te va a escribir por WhatsApp en unos minutos
          para ayudarte con tu declaración de Renta Natural 2026.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-6"
    >
      <div className="flex flex-col gap-1.5">
        <label htmlFor="full_name" className="text-sm font-semibold text-white/90">
          Nombre completo
        </label>
        <input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          className="rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-white placeholder-white/40 outline-none focus:border-teal-400"
          placeholder="Tu nombre"
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="whatsapp_phone" className="text-sm font-semibold text-white/90">
          Número de WhatsApp
        </label>
        <input
          id="whatsapp_phone"
          name="whatsapp_phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          value={phone}
          onChange={(event) => handlePhoneChange(event.target.value)}
          className="rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-white placeholder-white/40 outline-none focus:border-teal-400"
          placeholder="300 123 4567"
          required
        />
      </div>

      {/* Hidden campaign tag, carried from the ad link's ?source= query string
          (design.md Decision 5) — never shown or edited by the visitor. */}
      <input type="hidden" name="source" value={source || ""} />

      {errorMsg && (
        <p className="text-sm text-red-400" role="alert">
          {errorMsg}
        </p>
      )}

      <button
        type="submit"
        disabled={submitState === "submitting"}
        className="mt-2 rounded-lg bg-teal-400 px-4 py-2.5 font-bold text-slate-950 transition-colors hover:bg-teal-300 disabled:opacity-60"
      >
        {submitState === "submitting" ? "Enviando..." : "Quiero mi declaración de renta"}
      </button>
    </form>
  );
}
