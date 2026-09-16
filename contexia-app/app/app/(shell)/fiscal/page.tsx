import { fiscalMock } from "@/lib/mock/fiscal";
import { FiscalRiskStatusCard } from "@/components/fiscal/FiscalRiskStatusCard";
import { ExAnteDetectionCard } from "@/components/fiscal/ExAnteDetectionCard";
import { ShadowAuditCard } from "@/components/fiscal/ShadowAuditCard";
import { TaxThresholdsCard } from "@/components/fiscal/TaxThresholdsCard";
import { UpgradePlanBanner } from "@/components/shared/UpgradePlanBanner";

// "Pregúntale a Taty" (TatyEscalationCard) removed 2026-09-16, founder request — these are
// paying clients, who now have JARVIS (hyper-personalized per company) instead of a generic
// pointer to Taty.
export default function FiscalPage() {
  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop flex flex-col gap-gutter max-w-4xl mx-auto w-full mt-2">
      <UpgradePlanBanner />
      <FiscalRiskStatusCard status={fiscalMock.risk} />
      <ExAnteDetectionCard data={fiscalMock.exAnte} />
      <ShadowAuditCard data={fiscalMock.shadowAudit} />
      <TaxThresholdsCard thresholds={fiscalMock.thresholds} />
    </div>
  );
}
