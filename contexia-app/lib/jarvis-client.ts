import { authenticatedFetch } from "./authenticated-fetch";
import { config } from "./config";

export interface JarvisChatResponse {
  message: string;
  timestamp?: string;
}

export interface HermesStatusResponse {
  online: boolean;
  url: string;
  uptime_seconds?: number;
}

class JarvisClient {
  async chat(message: string): Promise<JarvisChatResponse> {
    const response = await authenticatedFetch(config.JARVIS_CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`Chat error: ${response.statusText}`);
    }

    return response.json();
  }

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
