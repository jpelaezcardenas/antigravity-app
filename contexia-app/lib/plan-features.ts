export type PlanTier = "freemium" | "starter" | "growth" | "enterprise";

type Feature =
  | "pulso_diario"
  | "centinela_alerts"
  | "liquidity_bridge"
  | "jarvis_chat"
  | "jarvis_voice";

const PLAN_FEATURES: Record<PlanTier, Set<Feature>> = {
  freemium: new Set(["pulso_diario"]),
  starter: new Set(["pulso_diario", "centinela_alerts", "liquidity_bridge"]),
  growth: new Set([
    "pulso_diario",
    "centinela_alerts",
    "liquidity_bridge",
    "jarvis_chat",
  ]),
  enterprise: new Set([
    "pulso_diario",
    "centinela_alerts",
    "liquidity_bridge",
    "jarvis_chat",
    "jarvis_voice",
  ]),
};

export function hasFeature(planTier: PlanTier, feature: Feature): boolean {
  const features = PLAN_FEATURES[planTier];
  return features ? features.has(feature) : false;
}
