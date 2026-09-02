/**
 * Client for the Shadow GL ingestion endpoints.
 * Used by DataUploadCard to upload files for real data ingestion.
 */

import { API_ENDPOINTS } from "./config";
import { authenticatedFetch } from "./authenticated-fetch";

export interface IngestionResult {
  success: boolean;
  row_count: number;
  date_range: string;
  error?: string;
}

/**
 * Upload a file (CSV, XLSX, XLS, XML, PDF) to the Shadow GL ingestion endpoint.
 *
 * The backend resolves the tenant from the caller's JWT — the file will be ingested
 * under the authenticated user's own tenant, not Cliente Cero.
 *
 * @param file - File to upload
 * @param isVerifiedReal - Set to true for genuine client data (false = test/synthetic)
 */
export async function uploadDataFile(
  file: File,
  isVerifiedReal: boolean = false
): Promise<IngestionResult> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_ENDPOINTS.uploadData}?is_verified_real=${isVerifiedReal}`;

  // Do NOT set Content-Type — browser sets it automatically with the correct boundary
  const response = await authenticatedFetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // ignore JSON parse error
    }
    return { success: false, row_count: 0, date_range: "", error: detail };
  }

  const data = await response.json();
  return {
    success: true,
    row_count: data.row_count ?? 0,
    date_range: data.date_range ?? "",
  };
}
