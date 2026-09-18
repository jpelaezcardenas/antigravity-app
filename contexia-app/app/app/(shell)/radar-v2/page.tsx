"use client";

import { useState } from "react";
import type { Scenario } from "@/lib/types/contexia";
import { radarMock } from "@/lib/mock/radar";
import { RadarScenarioSelector } from "@/components/radar/RadarScenarioSelector";
import { CashProjectionCard } from "@/components/radar/CashProjectionCard";
import { CashProjection13wCard } from "@/components/radar/CashProjection13wCard";
import { EstimatedTaxProvisionCard } from "@/components/radar/EstimatedTaxProvisionCard";
import { StrategicInsightCard } from "@/components/radar/StrategicInsightCard";
import { UpcomingMilestonesCard } from "@/components/radar/UpcomingMilestonesCard";
import { UpgradePlanBannerV2 } from "@/components/shared/v2/UpgradePlanBannerV2";
import { V2ConfigGearHeader } from "@/components/shared/v2/V2ConfigGearHeader";
import { JarvisFloatingBadgeV2 } from "@/components/jarvis/v2/JarvisFloatingBadgeV2";
import { RadarCashProjectionTiles } from "@/components/radar/v2/RadarCashProjectionTiles";

/**
 * PWA V2 visual pilot (Fase 3, reconstructed 2026-09-17) — the first cut of
 * this page kept radarMock's plain hero text ("Lo que viene") instead of the
 * Stitch-approved metric-tile grid. This version adds RadarCashProjectionTiles
 * — a tile summary of the SAME real fetchCashProjection13w() data the chart
 * below already renders, nothing new fetched or invented — right under the
 * hero, per Stitch. CashProjection13wCard (the real chart) and the mock
 * 90-day scenario cards stay below as deeper content.
 */
export default function RadarV2Page() {
  const [scenario, setScenario] = useState<Scenario>("base");
  const data = radarMock.scenarios[scenario];

  return (
    <div
      data-cx-ui="v2"
      className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2 pb-16"
    >
      <V2ConfigGearHeader />

      <UpgradePlanBannerV2 />

      <section className="flex flex-col gap-1.5">
        <p className="text-xs font-medium tracking-widest uppercase text-on-surface-variant/90">
          Radar de caja · 13 semanas
        </p>
        <h1 className="font-extralight tracking-tight text-white text-[40px] sm:text-[48px] leading-tight">
          Lo que viene
        </h1>
        <p className="text-sm text-on-surface-variant">{radarMock.header.subtitle}</p>
      </section>

      <JarvisFloatingBadgeV2 />

      <RadarCashProjectionTiles />

      <RadarScenarioSelector value={scenario} onChange={setScenario} />

      <CashProjection13wCard />

      <CashProjectionCard projection={data.cashProjection} />
      <EstimatedTaxProvisionCard provision={data.taxProvision} />
      <StrategicInsightCard insight={data.strategicInsight} />
      <UpcomingMilestonesCard milestones={data.upcomingMilestones} />
    </div>
  );
}
