import { PulsoHeroV2 } from "@/components/pulso/v2/PulsoHeroV2";
import { ActiveAlertsV2 } from "@/components/pulso/v2/ActiveAlertsV2";
import { DataUploadCard } from "@/components/pulso/DataUploadCard";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";

/**
 * PWA V2 visual pilot (Fase 3 de openspec/changes/pwa-v2-*, plan de migración).
 * Ruta de preview aislada — NO reemplaza /app/overview todavía. Reusa los
 * mismos contratos de datos reales (fetchFinancials/fetchCentinelaAlerts/
 * fetchTenantMe) que la pantalla de producción; solo cambia la composición
 * visual (jerarquía tipo Weather: cifra dominante + espacio negativo +
 * alertas). No incluye el insight card ni "Próximos Hitos" del mockup de
 * Stitch porque ninguno de los dos tiene respaldo en el backend hoy.
 */
export default function OverviewV2Page() {
  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-8 max-w-4xl mx-auto w-full mt-2 pb-16"
    >
      <PulsoHeroV2 />
      <JarvisFloatingBadgeV2 />
      <ActiveAlertsV2 />
      <div id="conectar-mis-datos" className="scroll-mt-24">
        <DataUploadCard />
      </div>
    </div>
  );
}
