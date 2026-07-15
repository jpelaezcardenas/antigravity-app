"use client";

import { patrimonio } from "@/lib/mock/patrimonio";
import { TotalEquityCard } from "@/components/patrimonio/TotalEquityCard";
import { StrategicPatrimonyInsightCard } from "@/components/patrimonio/StrategicPatrimonyInsightCard";
import { DividendShieldCard } from "@/components/patrimonio/DividendShieldCard";
import { WithdrawalSimulatorCard } from "@/components/patrimonio/WithdrawalSimulatorCard";
import { EquityMovementHistoryCard } from "@/components/patrimonio/EquityMovementHistoryCard";

export default function PatrimonioPage() {
  const data = patrimonio;

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-7xl mx-auto flex flex-col gap-6 w-full mt-2">
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
