/**
 * CRM/Ventas B2B retainer API client — the third data-bound exception to
 * contexia-app's mock-first rule, alongside CashTodayCard and Social Content
 * Ops (see CLAUDE.md "Pantallas data-bound"). Calls the canonical
 * `/api/v1/crm/*` backend on Railway (same origin as lib/social-ops-api.ts).
 */

import { API_BASE_URL } from "./config";

export interface B2bClient {
  id: string;
  name: string;
  status: "activo" | "inactivo";
  monthly_fee_cents: number | null;
}

export interface B2bClientsResponse {
  source: "supabase" | "demo_fallback";
  items: B2bClient[];
}

export interface B2bPaymentsGrid {
  clients: B2bClient[];
  periods: string[];
  cells: Record<string, Record<string, number>>;
}

export interface B2bPaymentsTotals {
  grand_total: number;
  by_period: Record<string, number>;
  by_client: Record<string, number>;
}

export interface B2bPaymentsResponse {
  source: "supabase" | "demo_fallback";
  grid: B2bPaymentsGrid;
  totals: B2bPaymentsTotals;
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

export function getB2bClients(): Promise<B2bClientsResponse> {
  return api<B2bClientsResponse>("/crm/b2b/clients");
}

export function getB2bPaymentsGrid(
  fromPeriod = "2026-01-01",
  toPeriod = "2026-06-30"
): Promise<B2bPaymentsResponse> {
  const params = new URLSearchParams({ from_period: fromPeriod, to_period: toPeriod });
  return api<B2bPaymentsResponse>(`/crm/b2b/payments?${params.toString()}`);
}

// B2C Renta Natural lead funnel (Change B: crm-b2c-sell-machine-cockpit)

export type CrmStage = "NUEVOS" | "PROSPECTOS" | "POR_APROBAR" | "LISTOS_CONTADORA";

export interface CrmLead {
  id: string;
  full_name: string | null;
  whatsapp_phone?: string | null;
  stage: CrmStage;
  score: number;
  last_message?: string | null;
}

export interface CrmPipelineColumn {
  id: CrmStage;
  label: string;
  leads: CrmLead[];
}

export interface CrmPipelineResponse {
  source: "supabase" | "demo_fallback";
  columns: CrmPipelineColumn[];
  summary: { total_leads: number };
}

export interface CrmTaxProfile {
  lead_id: string;
  es_asalariado: boolean | null;
  topes: Record<string, unknown>;
  rut_status: "pending" | "collected";
  extractos_status: "pending" | "collected";
  obligado_declarar: boolean | null;
}

export function getB2cPipeline(): Promise<CrmPipelineResponse> {
  return api<CrmPipelineResponse>("/crm/b2c/pipeline");
}

export function advanceCrmLead(leadId: string, stage: CrmStage): Promise<CrmLead> {
  return api<CrmLead>(`/crm/leads/${leadId}/advance`, {
    method: "POST",
    body: JSON.stringify({ stage }),
  });
}

export function getCrmTaxProfile(leadId: string): Promise<CrmTaxProfile> {
  return api<CrmTaxProfile>(`/crm/leads/${leadId}/tax-profile`);
}

export function updateCrmTaxProfile(
  leadId: string,
  patch: Partial<CrmTaxProfile>
): Promise<CrmTaxProfile> {
  return api<CrmTaxProfile>(`/crm/leads/${leadId}/tax-profile`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function approveCrmPayment(leadId: string, approvedBy: string): Promise<CrmLead> {
  return api<CrmLead>(`/crm/leads/${leadId}/approve-payment`, {
    method: "POST",
    body: JSON.stringify({ approved_by: approvedBy }),
  });
}
