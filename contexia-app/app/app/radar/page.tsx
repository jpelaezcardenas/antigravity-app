"use client";

import { useEffect, useState } from "react";
import type { Scenario } from "@/lib/types/contexia";
import { radarMock } from "@/lib/mock/radar";
import { fetchRadarScenarios, type RadarResponse } from "@/lib/services/api";
import { RadarScenarioSelector } from "@/components/radar/RadarScenarioSelector";
import { CashProjectionCard } from "@/components/radar/CashProjectionCard";
import { EstimatedTaxProvisionCard } from "@/components/radar/EstimatedTaxProvisionCard";
import { StrategicInsightCard } from "@/components/radar/StrategicInsightCard";
import { UpcomingMilestonesCard } from "@/components/radar/UpcomingMilestonesCard";

type DataSource = "live" | "mock";

export default function RadarPage() {
  const [scenario, setScenario] = useState<Scenario>("base");
  const [radar, setRadar] = useState<RadarResponse | null>(null);
  const [source, setSource] = useState<DataSource>("mock");

  useEffect(() => {
    let cancelled = false;
    fetchRadarScenarios("ctx-001")
      .then((data) => {
        if (cancelled) return;
        setRadar(data);
        setSource("live");
      })
      .catch((err) => {
        console.warn("Radar API unavailable, using mock:", err.message);
        if (cancelled) return;
        setSource("mock");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const header = radar?.header ?? radarMock.header;
  const data = radar?.scenarios[scenario] ?? radarMock.scenarios[scenario];

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2">
      <section className="flex flex-col gap-4">
        <div>
          <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-primary-container">
            {header.title}
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">
            {header.subtitle}
          </p>
          {source === "mock" && (
            <p className="text-xs text-on-surface-variant/70 mt-2 italic">
              Datos de ejemplo — backend no conectado
            </p>
          )}
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
