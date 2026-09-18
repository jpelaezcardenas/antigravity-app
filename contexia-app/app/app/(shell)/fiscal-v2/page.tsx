import { fiscalMock } from "@/lib/mock/fiscal";
import { TaxThresholdsCard } from "@/components/fiscal/TaxThresholdsCard";
import { UpgradePlanBannerV2 } from "@/components/shared/v2/UpgradePlanBannerV2";
import { V2ConfigGearHeader } from "@/components/shared/v2/V2ConfigGearHeader";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";
import { MetricTileGrid, type MetricTile } from "@/components/shared/v2/MetricTileGrid";

/**
 * PWA V2 visual pilot (Fase 3, reconstructed 2026-09-17) — the first cut of
 * this page reused old V1 card components (ExAnteDetectionCard,
 * ShadowAuditCard) verbatim with just a new hero on top, which is NOT what
 * was approved in Stitch: a compact metric-tile grid. This version uses a
 * tile grid for exactly the 2 fields fiscalMock actually has data for
 * (blocked invoices count, DIAN reconciliation %). The Stitch reference
 * design also showed "Próximo vencimiento", "Provisionado", "Facturas
 * emitidas/recibidas" tiles — none of those fields exist in fiscalMock or
 * anywhere in the backend, so they are deliberately NOT built here rather
 * than shipped as fabricated numbers (founder decision, 2026-09-17).
 * TaxThresholdsCard (real UVT thresholds) stays below as-is.
 */
export default function FiscalV2Page() {
  const tiles: MetricTile[] = [
    {
      id: "blocked-invoices",
      icon: "block",
      label: "Facturas bloqueadas",
      value: String(fiscalMock.exAnte.blockedCount),
      accent: "warning",
    },
    {
      id: "dian-reconciliation",
      icon: "verified",
      label: "Cuadre DIAN",
      value: fiscalMock.shadowAudit.highlight,
      accent: "success",
    },
  ];

  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-gutter max-w-4xl mx-auto w-full mt-2 pb-16"
    >
      <V2ConfigGearHeader />

      <UpgradePlanBannerV2 />

      <div className="flex flex-col gap-1.5">
        <p className="text-xs font-medium tracking-widest uppercase text-on-surface-variant/90">
          {fiscalMock.risk.sectionLabel}
        </p>
        <h1 className="font-extralight tracking-tight text-white text-[40px] sm:text-[48px] leading-tight">
          {fiscalMock.risk.levelLabel.split("·")[0].trim()}
        </h1>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container/60 border border-outline-variant/40 backdrop-blur-md w-fit">
          <span className="w-1.5 h-1.5 rounded-full bg-primary" />
          <span className="text-xs font-normal text-on-surface-variant tracking-wide">
            {fiscalMock.risk.levelLabel.split("·")[1]?.trim()}
          </span>
        </div>
      </div>

      <JarvisFloatingBadgeV2 />

      <MetricTileGrid tiles={tiles} />

      <div className="rounded-2xl border border-outline-variant/40 bg-surface-container/60 backdrop-blur-md p-4">
        <p className="text-sm text-white font-semibold mb-1">{fiscalMock.exAnte.title}</p>
        <p className="text-xs text-on-surface-variant">{fiscalMock.exAnte.description}</p>
      </div>

      <TaxThresholdsCard thresholds={fiscalMock.thresholds} />
    </div>
  );
}
