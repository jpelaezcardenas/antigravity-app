/**
 * API client para antigravity-app backend
 * Endpoint base: /api/v1
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080/api/v1";

// ============================================================================
// Radar - Scenario Projections
// ============================================================================

import type { Scenario, RadarScenarioData } from "@/lib/types/contexia";

export interface RadarResponse {
  header: { title: string; subtitle: string };
  scenarios: Record<Scenario, RadarScenarioData>;
  company_id: string;
  generated_at: string;
}

/**
 * Fetch 3-scenario fiscal projection from backend.
 * Throws on network/HTTP error — caller decides whether to fall back to mock.
 */
export async function fetchRadarScenarios(company_id: string): Promise<RadarResponse> {
  const url = new URL(`${API_BASE}/radar/scenarios`);
  url.searchParams.set("company_id", company_id);

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Radar API error: ${response.status}`);
  }
  return (await response.json()) as RadarResponse;
}

// ============================================================================
// Taty Contadora - Fiscal AI Agent
// ============================================================================

export interface Citation {
  source: string;
  fragment: string;
}

export interface TatyAskRequest {
  company_id: string;
  question: string;
  channel?: string;
  conversation_id?: string;
  user_id?: string;
}

export interface TatyAskResponse {
  answer: string;
  citations: Citation[];
  latency_ms: number;
  confidence: number;
  requires_human_review: boolean;
  result?: string; // Backward compat alias
}

/**
 * Pregunta a Taty Contadora sobre un tema fiscal
 */
export async function askTaty(request: TatyAskRequest): Promise<TatyAskResponse> {
  const url = new URL(`${API_BASE}/agents/taty/ask`);

  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        company_id: request.company_id,
        question: request.question,
        channel: request.channel || "dashboard",
        conversation_id: request.conversation_id,
        user_id: request.user_id,
      }),
    });

    if (!response.ok) {
      throw new Error(`Taty API error: ${response.status}`);
    }

    const data = (await response.json()) as TatyAskResponse;
    return data;
  } catch (error) {
    console.error("Error calling Taty API:", error);
    throw error;
  }
}

/**
 * GET alternative para dashboard (CORS-friendly)
 */
export async function askTatyGET(request: TatyAskRequest): Promise<TatyAskResponse> {
  const url = new URL(`${API_BASE}/agents/taty/ask`);
  url.searchParams.set("company_id", request.company_id);
  url.searchParams.set("question", request.question);
  url.searchParams.set("channel", request.channel || "dashboard");

  if (request.conversation_id) {
    url.searchParams.set("conversation_id", request.conversation_id);
  }
  if (request.user_id) {
    url.searchParams.set("user_id", request.user_id);
  }

  try {
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Taty API error: ${response.status}`);
    }

    const data = (await response.json()) as TatyAskResponse;
    return data;
  } catch (error) {
    console.error("Error calling Taty API (GET):", error);
    throw error;
  }
}

/**
 * Health check para Taty service
 */
export async function checkTatyHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/agents/taty/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// ============================================================================
// Centinela - Fiscal Risk Detection Engine
// ============================================================================

import type { CentinelaEvaluateRequest, CentinelaEvaluateResponse } from "@/lib/types/centinela";

/**
 * Evaluates fiscal risk using Centinela rules
 */
export async function evaluateCentinela(
  request: CentinelaEvaluateRequest
): Promise<CentinelaEvaluateResponse> {
  const url = new URL(`${API_BASE}/centinela/evaluate`);

  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        company_id: request.company_id,
        financial_data: request.financial_data,
        save_alerts: request.save_alerts ?? false,
      }),
    });

    if (!response.ok) {
      throw new Error(`Centinela API error: ${response.status}`);
    }

    const data = (await response.json()) as CentinelaEvaluateResponse;
    return data;
  } catch (error) {
    console.error("Error calling Centinela API:", error);
    throw error;
  }
}
