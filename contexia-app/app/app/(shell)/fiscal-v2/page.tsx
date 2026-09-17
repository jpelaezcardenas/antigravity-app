import { fiscalMock } from "@/lib/mock/fiscal";
import { ExAnteDetectionCard } from "@/components/fiscal/ExAnteDetectionCard";
import { ShadowAuditCard } from "@/components/fiscal/ShadowAuditCard";
import { TaxThresholdsCard } from "@/components/fiscal/TaxThresholdsCard";
import { UpgradePlanBanner } from "@/components/shared/UpgradePlanBanner";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";

/**
 * PWA V2 visual pilot (Fase 3) — reuses the exact real fiscalMock content and
 * existing components (ExAnteDetectionCard, ShadowAuditCard, TaxThresholdsCard)
 * verbatim, only adding the new hero framing above them. Nothing here is
 * invented — verified against fiscalMock.ts field by field.
 */
export default function FiscalV2Page() {
  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-gutter max-w-4xl mx-auto w-full mt-2 pb-16"
    >
      <UpgradePlanBanner />

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

      <ExAnteDetectionCard data={fiscalMock.exAnte} />
      <ShadowAuditCard data={fiscalMock.shadowAudit} />
      <TaxThresholdsCard thresholds={fiscalMock.thresholds} />
    </div>
  );
}
