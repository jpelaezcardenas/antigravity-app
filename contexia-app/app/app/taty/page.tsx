import { TatyView } from "@/components/taty/TatyView";

export const metadata = {
  title: "Taty - Asesora Fiscal IA | Contexia",
  description: "Pregunta a Taty sobre impuestos, DIAN, régimen tributario y más",
};

export default function TatyPage() {
  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-6 max-w-3xl mx-auto w-full py-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-headline-lg text-on-surface font-semibold">
          Taty - Asesora Fiscal IA
        </h1>
        <p className="text-body-md text-on-surface-variant">
          Tu asesora fiscal disponible 24/7. Pregunta sobre impuestos, DIAN, régimen
          tributario, retenciones, UVT y más.
        </p>
      </div>

      {/* Taty Widget */}
      <TatyView company_id="ctx-001" />

      {/* Info Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <div className="p-4 rounded-lg bg-surface-elevated border border-outline/30">
          <h3 className="font-semibold text-sm text-on-surface mb-2">
            📋 Fuentes confiables
          </h3>
          <p className="text-xs text-on-surface-variant">
            Taty se basa en normograma DIAN, estatuto tributario y documentos
            oficiales.
          </p>
        </div>
        <div className="p-4 rounded-lg bg-surface-elevated border border-outline/30">
          <h3 className="font-semibold text-sm text-on-surface mb-2">
            ⚠️ Escalaciones
          </h3>
          <p className="text-xs text-on-surface-variant">
            Si la pregunta requiere asesoría legal especializada, Taty lo indicará.
          </p>
        </div>
      </div>
    </div>
  );
}
