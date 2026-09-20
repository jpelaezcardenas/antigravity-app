"use client";
import { useMemo, useState } from "react";
import { useEcomStore } from "@/lib/ecomStore";
import {
  calcularIvaPerdidoMensual,
  excedeUmbralResponsableIVA,
  calcularTier,
} from "@/lib/ecomCalculations";
import { formatCOP } from "@/lib/calculations";
import EcomStepWrapper from "./EcomStepWrapper";

interface Props {
  onBack: () => void;
}

const WHATSAPP_NUMBER = "573106229289"; // same production number as TatyFloat.tsx

function buildWhatsAppUrl(ivaPerdidoMensual: number, tier: 1 | 2 | 3): string {
  const monto = formatCOP(ivaPerdidoMensual);
  const mensaje =
    tier === 1
      ? `Hola, hice el diagnóstico exprés de IVA y podría estar dejando ${monto} al mes sobre la mesa. Quiero unirme a los primeros 50 cupos de la Comunidad VIP para revisarlo con Taty.`
      : `Hola, hice el diagnóstico exprés de IVA (estimado ${monto}/mes) y quiero saber más sobre la Comunidad VIP de Contexia.`;
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(mensaje)}`;
}

export default function Step3Resultado({ onBack }: Props) {
  const { numeros, formalizacion, email, setEmail } = useEcomStore();
  const [emailInput, setEmailInput] = useState(email ?? "");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">(
    "idle"
  );

  const ventasMensuales = numeros.ventasMensuales ?? 0;
  const gastoMetaAds = numeros.gastoMetaAds ?? 0;

  const ivaPerdidoMensual = useMemo(
    () => calcularIvaPerdidoMensual(gastoMetaAds),
    [gastoMetaAds]
  );
  const excedeUmbral = useMemo(
    () => excedeUmbralResponsableIVA(ventasMensuales),
    [ventasMensuales]
  );
  const tier = useMemo(
    () => calcularTier(ventasMensuales, gastoMetaAds),
    [ventasMensuales, gastoMetaAds]
  );

  const semaforoColor = excedeUmbral ? "#ef4444" : "#22c55e";
  const semaforoLabel = excedeUmbral
    ? "Superas el umbral de responsable de IVA (3.500 UVT)"
    : "Estás por debajo del umbral de responsable de IVA (3.500 UVT)";

  const whatsappUrl = buildWhatsAppUrl(ivaPerdidoMensual, tier);

  // Best-effort, optional lead save (design.md D6) — the WhatsApp button
  // above never depends on this succeeding, or on this field being filled.
  const handleGuardarEmail = async () => {
    if (!emailInput.trim()) return;
    setEmail(emailInput.trim());
    setSaveState("saving");
    try {
      const res = await fetch("/wizard/api/leads/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paso1: { email: emailInput.trim() },
          source: "iva_ecom_express",
          feria_data: {
            iva_ecom_inputs: {
              ventasMensuales,
              gastoMetaAds,
              margenBruto: numeros.margenBruto,
              tipoPersona: formalizacion.tipoPersona,
              facturaElectronicamente: formalizacion.facturaElectronicamente,
              ivaPerdidoMensual,
              excedeUmbral,
              tier,
            },
          },
        }),
      });
      setSaveState(res.ok ? "saved" : "error");
    } catch {
      setSaveState("error");
    }
  };

  return (
    <EcomStepWrapper
      step={3}
      headline="Tu diagnóstico exprés"
      onBack={onBack}
      isLastStep
    >
      <div style={{ display: "grid", gap: "1.5rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "1rem",
            borderRadius: "12px",
            border: `1px solid ${semaforoColor}55`,
            background: `${semaforoColor}18`,
          }}
        >
          <div
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: semaforoColor,
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: "0.875rem", color: "var(--ctx-text)" }}>
            {semaforoLabel}
          </span>
        </div>

        <div style={{ textAlign: "center" }}>
          <p style={{ color: "var(--ctx-text-muted)", fontSize: "0.9375rem", margin: "0 0 0.5rem" }}>
            Si eres responsable de IVA y no lo estás reclamando, podrías estar dejando
            aproximadamente
          </p>
          <p
            className="font-orbitron"
            style={{ fontSize: "2rem", fontWeight: 800, color: "var(--ctx-teal)", margin: "0 0 0.5rem" }}
          >
            {formatCOP(ivaPerdidoMensual)} / mes
          </p>
          <p style={{ color: "var(--ctx-text-light)", fontSize: "0.8125rem", margin: 0 }}>
            Estimado sobre tu gasto en Meta Ads. No es un valor exacto ni una garantía —
            depende de tu condición de responsable de IVA y de cómo factures.
          </p>
        </div>

        <a
          href={whatsappUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="ctx-btn-primary"
          style={{
            display: "block",
            textAlign: "center",
            fontSize: "1rem",
            padding: "1rem",
            borderRadius: "12px",
          }}
        >
          Únete a los primeros 50 cupos — auditarlo con Taty →
        </a>

        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.08)",
            paddingTop: "1.25rem",
          }}
        >
          <label className="ctx-label">
            ¿Quieres que te enviemos este resultado por email? (opcional)
          </label>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
            <input
              type="email"
              className="ctx-input"
              placeholder="tu@email.com"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              style={{ flex: 1 }}
            />
            <button
              type="button"
              onClick={handleGuardarEmail}
              className="ctx-btn-secondary"
              disabled={saveState === "saving" || !emailInput.trim()}
            >
              {saveState === "saving" ? "Enviando..." : "Enviar"}
            </button>
          </div>
          {saveState === "saved" && (
            <p style={{ color: "var(--ctx-teal)", fontSize: "0.8125rem", marginTop: "0.5rem" }}>
              Listo, te lo enviamos en unos minutos.
            </p>
          )}
          {saveState === "error" && (
            <p style={{ color: "var(--ctx-text-muted)", fontSize: "0.8125rem", marginTop: "0.5rem" }}>
              No pudimos guardar tu email, pero puedes seguir por WhatsApp arriba.
            </p>
          )}
        </div>
      </div>
    </EcomStepWrapper>
  );
}
