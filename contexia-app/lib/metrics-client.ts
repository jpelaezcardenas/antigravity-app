import { API_ENDPOINTS } from "./config";
import { authenticatedFetch } from "./authenticated-fetch";

export interface DailyAutoApproval {
  date: string;
  approved: number;
  false_positives: number;
}

export interface AutoApprovalMetrics {
  days: number;
  total_auto_approved: number;
  by_rule: { recurring: number; vendor: number; micro: number };
  false_positives: number;
  daily: DailyAutoApproval[];
}

export interface DailyCSVIngestion {
  date: string;
  batches: number;
  rows_ok: number;
  rows_err: number;
}

export interface CSVIngestionMetrics {
  days: number;
  batches: number;
  rows_processed: number;
  rows_error: number;
  daily: DailyCSVIngestion[];
}

export interface QueueHealth {
  pending: number;
  avg_review_seconds: number | null;
}

export interface VendorEntry {
  vendor: string;
  count: number;
}

async function metricsGet<T>(url: string): Promise<T> {
  const res = await authenticatedFetch(url);
  if (!res.ok) throw new Error(`metrics fetch failed: ${res.status}`);
  return res.json();
}

export const fetchAutoApprovalMetrics = (days = 7) =>
  metricsGet<AutoApprovalMetrics>(`${API_ENDPOINTS.metricsAutoApproval}?days=${days}`);

export const fetchCSVIngestionMetrics = (days = 7) =>
  metricsGet<CSVIngestionMetrics>(`${API_ENDPOINTS.metricsCsvIngestion}?days=${days}`);

export const fetchQueueHealth = () =>
  metricsGet<QueueHealth>(API_ENDPOINTS.metricsQueueHealth);

export const fetchTopVendors = (limit = 10) =>
  metricsGet<VendorEntry[]>(`${API_ENDPOINTS.metricsTopVendors}?limit=${limit}`);
