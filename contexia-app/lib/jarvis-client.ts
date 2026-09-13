import { authenticatedFetch } from "./authenticated-fetch";
import { config } from "./config";

export interface HermesStatusResponse {
  // Matches the real backend contract (apps/backend/presentation/jarvis_endpoints.py::jarvis_status):
  // {"status": "ok", "gateway_url": ..., "hermes": {...}} on success,
  // {"status": "unreachable", "gateway_url"?: ..., "detail": ...} on failure.
  status: "ok" | "unreachable";
  gateway_url?: string;
  hermes?: { uptime_seconds?: number; [key: string]: unknown };
  detail?: string;
}

class JarvisClient {
  // No chat() method here: POST /api/v1/jarvis/chat is SSE-only (StreamingResponse,
  // never a single JSON body) — JarvisChatInterface.tsx reads the stream directly
  // with fetch()/getReader() instead of going through this client. A `chat()` that
  // called `.json()` on that response would always throw; removed rather than left
  // as a trap (config.JARVIS_CHAT_URL is unused for the same reason).

  async status(): Promise<HermesStatusResponse> {
    const response = await authenticatedFetch(config.JARVIS_STATUS_URL, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`Status error: ${response.statusText}`);
    }

    return response.json();
  }
}

export const jarvisClient = new JarvisClient();
