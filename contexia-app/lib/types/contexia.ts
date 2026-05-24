/**
 * Core Contexia domain types
 */

export type Scenario = "pesimista" | "base" | "optimista";
export type StatusLevel = "sana" | "vigilancia" | "alerta" | "crítica";

// Pulso (Dashboard)
export interface PulsoNote {
  title: string;
  message: string;
  sentiment: "positive" | "neutral" | "negative";
}

export interface CashPosition {
  available: number;
  reserved: number;
  forecast: number;
}

export interface HealthMetric {
  liquidity: number;
  profitability: number;
  efficiency: number;
  growth: number;
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: "info" | "warning" | "error";
}

// Fiscal
export interface RiskData {
  level: "low" | "medium" | "high";
  score: number;
  alerts: number;
}

export interface ExAnteData {
  violations: string[];
  recommendations: string[];
}

export interface ShadowAuditData {
  findings: string[];
}

export interface ThresholdData {
  limit: number;
  used: number;
  percent: number;
}

export interface TatyData {
  lastQuestion: string | null;
}

// Radar (Scenarios)
export interface CashProjection {
  forecast: number;
  baselineDate: string;
  scenarios: {
    pesimista: number;
    base: number;
    optimista: number;
  };
}

export interface TaxProvision {
  estimatedMonthly: number;
  estimatedQuarterly: number;
  notes: string;
}

export interface StrategicInsight {
  title: string;
  description: string;
  actionItems: string[];
}

export interface Milestone {
  date: string;
  description: string;
  impact: "low" | "medium" | "high";
}

export interface RadarScenarioData {
  cashProjection: CashProjection;
  taxProvision: TaxProvision;
  strategicInsight: StrategicInsight;
  upcomingMilestones: Milestone[];
}
