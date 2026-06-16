import { createHmac } from 'crypto';

const HERMES_GATEWAY_URL = process.env.NEXT_PUBLIC_HERMES_GATEWAY_URL || 'https://sharp-peas-cry.loca.lt';
const HERMES_WEBHOOK_SECRET = process.env.HERMES_WEBHOOK_SECRET || '';

function computeHmacSignature(secret: string, payload: string): string {
  return createHmac('sha256', secret).update(payload).digest('base64');
}

export default async function handler(req: Request) {
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405 });
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
        // localtunnel shows an interstitial page to cloud IPs without this header
        'bypass-tunnel-reminder': 'true',
        'User-Agent': 'contexia-bunker/1.0',
      },
      body: payload,
      signal: controller.signal,
    }).finally(() => clearTimeout(timeout));

    const data = await gatewayResponse.json();

    return new Response(JSON.stringify({
      status: 'success',
      data,
      gateway_url: HERMES_GATEWAY_URL,
      timestamp: new Date().toISOString(),
    }), {
      status: gatewayResponse.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Hermes gateway request failed:', errorMessage);

    return new Response(JSON.stringify({
      error: 'Gateway unavailable',
      message: errorMessage,
      gateway_url: HERMES_GATEWAY_URL,
    }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
