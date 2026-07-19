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
