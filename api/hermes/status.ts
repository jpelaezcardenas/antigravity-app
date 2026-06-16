/**
 * Hermes Gateway Proxy
 * El Bunker (frontend Vercel) llama este endpoint para hablar con el Hermes Gateway local
 * vía el túnel público (cloudflared). Classic Vercel Node function: firma (req, res).
 *
 * POST /api/hermes/status → Vercel function → cloudflared tunnel → localhost:8644/webhooks/os-status
 */

import { createHmac } from 'crypto';

// Minimal request/response shape for Vercel's classic Node runtime (no @vercel/node dep installed)
type Req = { method?: string };
type Res = {
  status: (code: number) => Res;
  json: (body: unknown) => void;
};

// Fallback URL (env var) used only if the Supabase lookup fails.
const HERMES_GATEWAY_URL_FALLBACK =
  process.env.NEXT_PUBLIC_HERMES_GATEWAY_URL || 'https://ladder-sheet-suggested-buys.trycloudflare.com';
const HERMES_WEBHOOK_SECRET = process.env.HERMES_WEBHOOK_SECRET || '';

// The cloudflared quick-tunnel URL is ephemeral. The PC-side wrapper writes the
// current URL into Supabase (table public.hermes_tunnel) on every tunnel start,
// so this function resolves it at runtime — no redeploy needed when it rotates.
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://kpynymwghfwshvcvevxq.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || '';

// In-memory cache so we don't hit Supabase on every request (per warm instance).
let cachedUrl: { value: string; at: number } | null = null;
const URL_CACHE_TTL_MS = 30_000;

async function resolveGatewayUrl(): Promise<string> {
  if (cachedUrl && Date.now() - cachedUrl.at < URL_CACHE_TTL_MS) {
    return cachedUrl.value;
  }
  if (!SUPABASE_ANON_KEY) {
    return HERMES_GATEWAY_URL_FALLBACK;
  }
  try {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 4000);
    const resp = await fetch(
      `${SUPABASE_URL}/rest/v1/hermes_tunnel?id=eq.current&select=url`,
      {
        headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` },
        signal: controller.signal,
      },
    ).finally(() => clearTimeout(t));
    const rows = (await resp.json()) as Array<{ url?: string }>;
    const url = rows?.[0]?.url;
    if (url) {
      cachedUrl = { value: url, at: Date.now() };
      return url;
    }
  } catch {
    // fall through to fallback
  }
  return HERMES_GATEWAY_URL_FALLBACK;
}

function computeHmacSignature(secret: string, payload: string): string {
  // Hermes generic webhook scheme: hex HMAC-SHA256 over the raw body
  return createHmac('sha256', secret).update(payload).digest('hex');
}

export default async function handler(req: Req, res: Res): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const gatewayUrl = await resolveGatewayUrl();

  try {
    const payload = JSON.stringify({
      timestamp: new Date().toISOString(),
      source: 'bunker-vercel',
    });

    const signature = computeHmacSignature(HERMES_WEBHOOK_SECRET, payload);

    // 8s abort guard so we fail fast instead of hitting Vercel's function timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    const gatewayResponse = await fetch(`${gatewayUrl}/webhooks/os-status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Hermes generic webhook auth: X-Webhook-Signature = hex HMAC-SHA256(body)
        'X-Webhook-Signature': signature,
        // cloudflared/localtunnel interstitial bypass + non-browser UA
        'bypass-tunnel-reminder': 'true',
        'User-Agent': 'contexia-bunker/1.0',
      },
      body: payload,
      signal: controller.signal,
    }).finally(() => clearTimeout(timeout));

    const data = await gatewayResponse.json().catch(() => ({}));

    res.status(gatewayResponse.status).json({
      status: 'success',
      data,
      gateway_url: gatewayUrl,
      timestamp: new Date().toISOString(),
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Hermes gateway request failed:', errorMessage);

    res.status(502).json({
      error: 'Gateway unavailable',
      message: errorMessage,
      gateway_url: gatewayUrl,
    });
  }
}
