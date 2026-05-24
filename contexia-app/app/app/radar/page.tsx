"use client";

import { useState } from "react";
import type { Scenario } from "@/lib/types/contexia";
import { radarMock } from "@/lib/mock/radar";
import { RadarScenarioSelector } from "@/components/radar/RadarScenarioSelector";
import { CashProjectionCard } from "@/components/radar/CashProjectionCard";
import { EstimatedTaxProvisionCard } from "@/components/radar/EstimatedTaxProvisionCard";
import { StrategicInsightCard } from "@/components/radar/StrategicInsightCard";
import { UpcomingMilestonesCard } from "@/components/radar/UpcomingMilestonesCard";

export default function RadarPage() {
  const [scenario, setScenario] = useState<Scenario>("base");
  const data = radarMock.scenarios[scenario];

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2">
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

      <CashProjectionCard projection={data.cashProjection} />
      <EstimatedTaxProvisionCard provision={data.taxProvision} />
      <StrategicInsightCard insight={data.strategicInsight} />
      <UpcomingMilestonesCard milestones={data.upcomingMilestones} />
    </div>
  );
}
