"use client";

import { patrimonio } from "@/lib/mock/patrimonio";
import { TotalEquityCard } from "@/components/patrimonio/TotalEquityCard";
import { StrategicPatrimonyInsightCard } from "@/components/patrimonio/StrategicPatrimonyInsightCard";
import { DividendShieldCard } from "@/components/patrimonio/DividendShieldCard";
import { WithdrawalSimulatorCard } from "@/components/patrimonio/WithdrawalSimulatorCard";
import { EquityMovementHistoryCard } from "@/components/patrimonio/EquityMovementHistoryCard";
import { UpgradePlanBanner } from "@/components/shared/UpgradePlanBanner";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";

export default function PatrimonioPage() {
  const data = patrimonio;

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2">
      <UpgradePlanBanner />
      <section className="flex flex-col gap-4">
        <div>
          <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-primary-container">
            {data.header.title}
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">
            {data.header.subtitle}
          </p>
        </div>
      </section>

      {/* JARVIS (2026-09-18): in-flow, right after the header/hero section — see
          overview/page.tsx for the full rationale. Mobile-only — DesktopSidebar already
          hosts the desktop access point on this `(shell)` layout. */}
      <div className="md:hidden">
        <JarvisFloatingBadgeV2 />
      </div>

      <TotalEquityCard patrimonio={data.patrimonio} />
      <StrategicPatrimonyInsightCard insight={data.insight} />
      <DividendShieldCard shield={data.dividendShield} />
      <WithdrawalSimulatorCard
        initialWithdrawal={data.withdrawalSimulator}
        cashWithoutWithdrawal={data.withdrawalSimulator.cashWithoutWithdrawal}
      />
      <EquityMovementHistoryCard movements={data.movements} />
    </div>
  );
}
