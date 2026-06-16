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

const HERMES_GATEWAY_URL =
  process.env.NEXT_PUBLIC_HERMES_GATEWAY_URL || 'https://ladder-sheet-suggested-buys.trycloudflare.com';
const HERMES_WEBHOOK_SECRET = process.env.HERMES_WEBHOOK_SECRET || '';

function computeHmacSignature(secret: string, payload: string): string {
  return createHmac('sha256', secret).update(payload).digest('base64');
}

export default async function handler(req: Req, res: Res): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const payload = JSON.stringify({
      timestamp: new Date().toISOString(),
      source: 'bunker-vercel',
    });

    const signature = computeHmacSignature(HERMES_WEBHOOK_SECRET, payload);

    // 8s abort guard so we fail fast instead of hitting Vercel's function timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    const gatewayResponse = await fetch(`${HERMES_GATEWAY_URL}/webhooks/os-status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Hermes-Signature': signature,
        // localtunnel/cloudflared interstitial bypass + non-browser UA
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
      gateway_url: HERMES_GATEWAY_URL,
      timestamp: new Date().toISOString(),
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Hermes gateway request failed:', errorMessage);

    res.status(502).json({
      error: 'Gateway unavailable',
      message: errorMessage,
      gateway_url: HERMES_GATEWAY_URL,
    });
  }
}
