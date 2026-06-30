/**
 * API Configuration for Contexia frontend
 *
 * Base URL defaults to Railway production backend.
 * Override via NEXT_PUBLIC_API_BASE_URL environment variable at build time.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "https://antigravity-app-production-175a.up.railway.app";

export const API_ENDPOINTS = {
  financials: `${API_BASE_URL}/api/v1/financials`,
};
