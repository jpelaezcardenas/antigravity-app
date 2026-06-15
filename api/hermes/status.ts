/**
 * Hermes Gateway Proxy
 * Endpoint que el Bunker (frontend Vercel) usa para comunicarse con Hermes Gateway local
 * vía el túnel público (localtunnel).
 *
 * POST /api/hermes/status → Vercel function → HTTPS tunnel → localhost:8644/webhooks/os-status
 */

import { VercelRequest, VercelResponse } from '@vercel/node';
import * as crypto from 'crypto';

const HERMES_GATEWAY_URL = process.env.NEXT_PUBLIC_HERMES_GATEWAY_URL || 'https://sharp-peas-cry.loca.lt';
const HERMES_WEBHOOK_SECRET = process.env.HERMES_WEBHOOK_SECRET || '';

if (!HERMES_WEBHOOK_SECRET) {
  console.warn('⚠️ HERMES_WEBHOOK_SECRET not set in env — HMAC validation will fail');
}

/**
 * Computa el HMAC-SHA256 esperado para el webhook de Hermes
 */
function computeHmacSignature(secret: string, payload: string): string {
  return crypto.createHmac('sha256', secret).update(payload).digest('base64');
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
): Promise<void> {
  // Solo POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Payload a enviar al webhook de Hermes
    const payload = JSON.stringify({
      timestamp: new Date().toISOString(),
      source: 'bunker-vercel',
    });

    // Computar firma HMAC
    const signature = computeHmacSignature(HERMES_WEBHOOK_SECRET, payload);

    // Hacer request al Hermes Gateway vía el túnel
    const gatewayResponse = await fetch(`${HERMES_GATEWAY_URL}/webhooks/os-status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Hermes-Signature': signature,
      },
      body: payload,
    });

    // Parsear respuesta
    const data = await gatewayResponse.json();

    // Retornar estado al frontend
    return res.status(gatewayResponse.status).json({
      status: 'success',
      data,
      gateway_url: HERMES_GATEWAY_URL,
      timestamp: new Date().toISOString(),
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('❌ Hermes gateway request failed:', errorMessage);

    return res.status(502).json({
      error: 'Gateway unavailable',
      message: errorMessage,
      gateway_url: HERMES_GATEWAY_URL,
    });
  }
}
