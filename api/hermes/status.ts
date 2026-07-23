/**
 * Hermes Gateway Proxy
 * El Bunker (frontend Vercel) llama este endpoint para hablar con el Hermes Gateway local
 * vía el túnel público (cloudflared). Classic Vercel Node function: firma (req, res).
 *
 * POST /api/hermes/status → Vercel function → cloudflared tunnel → localhost:8644/health
 *
 * Corrected 2026-07-22: the gateway's generic webhook platform (platforms.webhook,
 * gateway/platforms/webhook.py) only exposes POST /webhooks/{route_name} for
 * configured, HMAC-signed routes that get turned into real agent turns — there
 * is no "os-status" route, and `deliver_only` routes require a real delivery
 * target (telegram/discord/slack/etc.), not a bare status ack. The module also
 * registers an unauthenticated GET /health ({"status":"ok","platform":"webhook"})
 * purpose-built for exactly this liveness check, so we call that instead of
 * inventing/signing a custom route. HERMES_WEBHOOK_SECRET is no longer used here.
 */

// Minimal request/response shape for Vercel's classic Node runtime (no @vercel/node dep installed)
type Req = { method?: string; headers?: Record<string, string | string[] | undefined> };
type Res = {
  status: (code: number) => Res;
  json: (body: unknown) => void;
};

// Fallback URL (env var) used only if the Supabase lookup fails.
const HERMES_GATEWAY_URL_FALLBACK =
  process.env.NEXT_PUBLIC_HERMES_GATEWAY_URL || 'https://ladder-sheet-suggested-buys.trycloudflare.com';

// The cloudflared quick-tunnel URL is ephemeral. The PC-side wrapper writes the
// current URL into Supabase (table public.hermes_tunnel) on every tunnel start,
// so this function resolves it at runtime — no redeploy needed when it rotates.
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://kpynymwghfwshvcvevxq.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || '';

// T23 (hermes-multi-tenant-wrapper): shared-secret gate on this endpoint so it
// isn't openly scannable/abusable by bots hitting the tunnel to the local
// Hermes gateway. Not a strong boundary (the token ships to the browser via
// NEXT_PUBLIC_HERMES_TUNNEL_TOKEN for the Bunker's own same-origin call) —
// it stops anonymous internet traffic, which is the actual threat here.
const HERMES_TUNNEL_TOKEN = process.env.HERMES_TUNNEL_TOKEN || '';

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

export default async function handler(req: Req, res: Res): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  if (HERMES_TUNNEL_TOKEN) {
    const authHeader = req.headers?.authorization;
    const provided = Array.isArray(authHeader) ? authHeader[0] : authHeader;
    const token = provided?.startsWith('Bearer ') ? provided.slice('Bearer '.length) : undefined;
    if (token !== HERMES_TUNNEL_TOKEN) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }
  }

  const gatewayUrl = await resolveGatewayUrl();

  try {
    // 8s abort guard so we fail fast instead of hitting Vercel's function timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    const gatewayResponse = await fetch(`${gatewayUrl}/health`, {
      method: 'GET',
      headers: {
        // cloudflared/localtunnel interstitial bypass + non-browser UA
        'bypass-tunnel-reminder': 'true',
        'User-Agent': 'contexia-bunker/1.0',
      },
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
