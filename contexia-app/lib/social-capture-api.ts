/**
 * Client for the public, unauthenticated social-lead-capture endpoint
 * (b2c-social-lead-capture, Task 4). Deliberately does NOT use
 * `authenticated-fetch.ts` — a visitor landing on the public
 * `/renta-natural` ad page has no session/token at all, and this endpoint
 * (`presentation/social_capture_endpoints.py`) never requires one; it always
 * resolves to Cliente Cero server-side.
 */

import { API_ENDPOINTS } from "./config";

export interface SocialCaptureResult {
  isNew: boolean;
  throttledRepeat: boolean;
}

/**
 * Fires the partial/full capture write. Called twice from the landing form:
 * once the moment the phone number becomes valid (partial capture, no
 * `fullName` yet), and again on full form submission (with `fullName`). The
 * backend's phone throttle makes the second call a safe no-op rather than a
 * duplicate lead or a duplicate first-contact WhatsApp send.
 */
export async function submitSocialCapture(input: {
  whatsappPhone: string;
  fullName?: string;
  source?: string;
}): Promise<SocialCaptureResult> {
  const response = await fetch(API_ENDPOINTS.socialCapturePartial, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      whatsapp_phone: input.whatsappPhone,
      full_name: input.fullName || undefined,
      source: input.source || undefined,
    }),
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  const data = (await response.json()) as {
    is_new?: boolean;
    throttled_repeat?: boolean;
  };

  return {
    isNew: Boolean(data.is_new),
    throttledRepeat: Boolean(data.throttled_repeat),
  };
}
