/**
 * Shared authenticated-fetch helper (bunker-pwa-auth-enforcement).
 *
 * Attaches `Authorization: Bearer <token>` to every data-bound request, reading the token from
 * `localStorage["token"]` — the same key the real `login.html` (Supabase Auth sign-in) already
 * populates on a successful login. Deliberately minimal: no redirect-to-login or session-clearing
 * logic here — that's already `middleware.ts`'s job at the Vercel edge (server-side, stronger than
 * anything this client helper could add), so this helper doesn't duplicate or race it.
 *
 * Every data-bound API client (lib/api-client.ts, lib/social-ops-api.ts, lib/crm-api.ts,
 * lib/sell-machine-api.ts) calls this instead of the native fetch.
 */

const TOKEN_KEY = "token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export async function authenticatedFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(input, { ...init, headers });
}
