export type SeverityLevel = "warning" | "critical";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface CentinelaEvidence {
  [key: string]: unknown;
}

export interface CentinelaAlert {
  rule_id: string;
  rule_name: string;
  severity: SeverityLevel;
  title: string;
  description: string;
  recommendation: string;
  evidence: CentinelaEvidence;
  company_id?: string;
}

export interface CentinelaEvaluateRequest {
  company_id: string;
  financial_data: Record<string, unknown>;
  save_alerts?: boolean;
}

export interface CentinelaEvaluateResponse {
  company_id: string;
  alerts: CentinelaAlert[];
  alert_count: number;
  critical_count: number;
  warning_count: number;
  risk_level: RiskLevel;
  saved_alert_ids: string[];
}
