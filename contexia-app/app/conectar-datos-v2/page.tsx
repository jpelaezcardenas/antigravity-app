import Link from "next/link";
import { DataUploadCard } from "@/components/pulso/DataUploadCard";

/**
 * Dedicated destination for Pulso-v2's "+" (2026-09-18) — the founder first
 * asked for the "+" to be the only way to reach "Conectar mis datos" (it was
 * duplicated with the card sitting always-visible inline), then clarified
 * further: "+" should NAVIGATE here, not just toggle the same card in/out of
 * the Pulso page ("quiero que al pulsar mas nos dirija a cargar los datos,
 * no que aparezca o desaparezca esta opcion de la v2"). Same detail-screen
 * shape as flujo-detalle-v2 (own layout, outside the (shell) group, no
 * BottomNav — browser back returns to Pulso).
 */
export default function ConectarDatosV2Page() {
  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop max-w-2xl mx-auto flex flex-col gap-6 w-full pb-12"
    >
      <div className="flex items-center gap-3">
        <Link
          href="/app/overview-v2"
          aria-label="Volver a Pulso"
          className="text-on-surface-variant hover:text-white transition-colors flex items-center justify-center h-10 w-10 -ml-2"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </Link>
        <p className="text-xs font-medium tracking-widest uppercase text-on-surface-variant/90">
          Conectar mis datos
        </p>
      </div>

      <DataUploadCard />
    </div>
  );
}
