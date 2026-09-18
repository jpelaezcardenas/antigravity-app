import { PulsoHeroV2 } from "@/components/pulso/v2/PulsoHeroV2";
import { ActiveAlertsV2 } from "@/components/pulso/v2/ActiveAlertsV2";
import { NextMilestonesV2 } from "@/components/pulso/v2/NextMilestonesV2";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";

/**
 * PWA V2 visual pilot (Fase 3 de openspec/changes/pwa-v2-*, plan de migración).
 * Ruta de preview aislada — NO reemplaza /app/overview todavía. Reusa los
 * mismos contratos de datos reales (fetchFinancials/fetchCentinelaAlerts/
 * fetchTenantMe) que la pantalla de producción; solo cambia la composición
 * visual (jerarquía tipo Weather: cifra dominante + espacio negativo +
 * alertas).
 *
 * Orden de scroll (confirmado 2026-09-18 contra la captura completa del
 * fundador): mitad superior = PulsoHeroV2 (cifra + insight IA real, rule-
 * based) + JARVIS; mitad inferior = ActiveAlertsV2 + NextMilestonesV2 (DIAN,
 * fecha real sin monto — no existe monto real por tenant en el esquema).
 *
 * "Conectar mis datos" (2026-09-18) ya no vive en esta pantalla: el "+" del
 * header de PulsoHeroV2 navega a `/app/conectar-datos-v2` (pantalla detalle
 * dedicada, mismo patrón que flujo-detalle-v2) — el fundador pidió que "+"
 * dirija ahí en vez de mostrar/ocultar la tarjeta dentro de Pulso.
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
      <NextMilestonesV2 />
    </div>
  );
}
