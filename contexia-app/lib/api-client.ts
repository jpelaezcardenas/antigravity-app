/**
 * API client for Contexia's Pulso diario financials endpoint.
 */

import { API_ENDPOINTS } from "./config";

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
  const response = await fetch(API_ENDPOINTS.financials, {
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
