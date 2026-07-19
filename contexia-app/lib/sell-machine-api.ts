/**
 * Sell Machine API client — the fifth data-bound exception to contexia-app's mock-first rule
 * (see CLAUDE.md "Pantallas data-bound"). Calls the canonical `/api/v1/sell-machine/*` and
 * `/api/v1/approval-queue/*` backend on Railway.
 */

import { API_BASE_URL } from "./config";

export interface Hook {
  headline: string;
  body: string;
  cta: string;
  pain_tag: string;
}

export interface CampaignPackage {
  id: string;
  draft_id: string;
  draft_type: string;
  status: string;
  reason: string;
  payload: {
    hooks: Hook[];
    creative_brief: string;
    target_segment: string;
    budget_cents: number | null;
  };
  created_at: string;
}

const API_BASE = `${API_BASE_URL}/api/v1`;

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: init?.body ? { "Content-Type": "application/json", ...init.headers } : init?.headers,
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function generateHooks(count = 5): Promise<{ hooks: Hook[] }> {
  return api<{ hooks: Hook[] }>("/sell-machine/hooks/generate", {
    method: "POST",
    body: JSON.stringify({ count }),
  });
}

export function evaluateHooks(hooks: Hook[]): Promise<{ survivors: Hook[] }> {
  return api<{ survivors: Hook[] }>("/sell-machine/hooks/evaluate", {
    method: "POST",
    body: JSON.stringify({ hooks }),
  });
}

export function createCampaignPackage(payload: {
  hooks: Hook[];
  brief: string;
  target_segment: string;
  budget?: number | null;
}): Promise<CampaignPackage> {
  return api<CampaignPackage>("/sell-machine/campaigns", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listCampaigns(status?: string): Promise<CampaignPackage[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  return api<CampaignPackage[]>(`/sell-machine/campaigns${params}`);
}

// Reuses the existing, unmodified Approval Queue endpoints (not Sell-Machine-specific — see
// design.md Decision 1/Task 6.1).
export function approveCampaignPackage(decisionId: string, approvedBy: string): Promise<unknown> {
  return api("/approval-queue/approve", {
    method: "POST",
    body: JSON.stringify({ decision_id: decisionId, reason: "Approved from Sell Machine", approved_by: approvedBy }),
  });
}

export function rejectCampaignPackage(decisionId: string, reason: string, rejectedBy: string): Promise<unknown> {
  return api("/approval-queue/reject", {
    method: "POST",
    body: JSON.stringify({ decision_id: decisionId, reason, rejected_by: rejectedBy }),
  });
}
