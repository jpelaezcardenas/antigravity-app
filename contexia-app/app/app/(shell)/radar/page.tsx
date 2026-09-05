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
import { UpgradePlanBanner } from "@/components/shared/UpgradePlanBanner";

export default function RadarPage() {
  const [scenario, setScenario] = useState<Scenario>("base");
  const data = radarMock.scenarios[scenario];

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2">
      <UpgradePlanBanner />
      <section className="flex flex-col gap-4">
        <div>
          <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-primary-container">
            {radarMock.header.title}
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">
            {radarMock.header.subtitle}
          </p>
        </div>
        <RadarScenarioSelector value={scenario} onChange={setScenario} />
      </section>

      {/* Live 13-week projection (radar-cash-projection-13w) — reads the real
          Shadow GL. The scenario-driven mock cards below are unaffected. */}
      <CashProjection13wCard />

      <CashProjectionCard projection={data.cashProjection} />
      <EstimatedTaxProvisionCard provision={data.taxProvision} />
      <StrategicInsightCard insight={data.strategicInsight} />
      <UpcomingMilestonesCard milestones={data.upcomingMilestones} />
    </div>
  );
}
