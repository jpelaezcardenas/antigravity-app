/**
 * API client for Contexia's Pulso diario financials endpoint.
 */

import { API_ENDPOINTS } from "./config";
import { authenticatedFetch } from "./authenticated-fetch";

export interface FinancialsSnapshot {
  caja_real: number; // COP minor units (cents) — cumulative bank balance as of today
  dinero_disponible: number; // COP minor units
  ventas_ayer: number; // COP minor units — income dated exactly yesterday
  gastos_ayer: number; // COP minor units — expenses dated exactly yesterday
  status: "healthy" | "empty";
}

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchFinancials(): Promise<FinancialsSnapshot> {
  const response = await authenticatedFetch(API_ENDPOINTS.financials, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, `Failed to fetch financials: ${error}`);
  }

  return response.json();
}

export interface CentinelaAlert {
  rule_id: string;
  rule_name: string;
  severity: string; // "info" | "warning" | "critical"
  title: string;
  description: string;
  recommendation?: string | null;
  evidence: Record<string, unknown>;
}

export interface CentinelaAlertsResponse {
  alerts: CentinelaAlert[];
  alert_count: number;
  critical_count: number;
  warning_count: number;
  risk_level: string; // "none" | "low" | "medium" | "high" | "critical"
  source: string; // "supabase" — this route never demo-falls-back
}

export interface LiquidityBridgeSnapshot {
  initial_balance: number; // COP minor units
  inflows: number; // COP minor units
  outflows: number; // COP minor units
  final_balance: number; // COP minor units
  period: string; // "YYYY-MM"
  status: "ready" | "empty";
}

export async function fetchCentinelaAlerts(): Promise<CentinelaAlertsResponse> {
  const response = await authenticatedFetch(API_ENDPOINTS.centinelaAlerts, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, `Failed to fetch centinela alerts: ${error}`);
  }

  return response.json();
}

export async function fetchLiquidityBridge(): Promise<LiquidityBridgeSnapshot> {
  const response = await authenticatedFetch(API_ENDPOINTS.liquidityBridge, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, `Failed to fetch liquidity bridge: ${error}`);
  }

  return response.json();
}
