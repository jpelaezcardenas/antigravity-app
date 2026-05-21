import crypto from "crypto";
import type { WompiWebhookEvent } from "./types";

const WOMPI_ENV = (process.env.WOMPI_ENV || "sandbox").toLowerCase();

export const WOMPI_BASE_URL =
  WOMPI_ENV === "production"
    ? "https://production.wompi.co/v1"
    : "https://sandbox.wompi.co/v1";

export const WOMPI_WIDGET_URL = "https://checkout.wompi.co/widget.js";

const INTEGRITY_SECRET = process.env.WOMPI_INTEGRITY_SECRET || "";
const EVENTS_SECRET = process.env.WOMPI_EVENTS_SECRET || "";

/**
 * Wompi requires SHA256(reference + amountInCents + currency + integritySecret)
 * sent with the widget call so the merchant signs the amount server-side.
 */
export function createIntegritySignature(
  reference: string,
  amountInCents: number,
  currency = "COP"
): string {
  if (!INTEGRITY_SECRET) {
    throw new Error("WOMPI_INTEGRITY_SECRET not configured");
  }
  const payload = `${reference}${amountInCents}${currency}${INTEGRITY_SECRET}`;
  return crypto.createHash("sha256").update(payload).digest("hex");
}

/**
 * Webhook signature check: concatenate the values of the properties listed in
 * `event.signature.properties` (in order), append the event timestamp, append
 * the events secret, hash with SHA256, compare to `event.signature.checksum`.
 * Docs: https://docs.wompi.co/docs/colombia/eventos/
 */
export function verifyWebhookSignature(event: WompiWebhookEvent): boolean {
  if (!EVENTS_SECRET) {
    console.error("WOMPI_EVENTS_SECRET not configured");
    return false;
  }
  const { properties, checksum } = event.signature;
  const concatenated = properties
    .map((p) => readByPath(event.data, p))
    .map((v) => (v === null || v === undefined ? "" : String(v)))
    .join("");
  const payload = `${concatenated}${event.timestamp}${EVENTS_SECRET}`;
  const expected = crypto.createHash("sha256").update(payload).digest("hex");
  return safeEqual(expected, checksum);
}

function readByPath(obj: unknown, path: string): unknown {
  return path
    .split(".")
    .reduce<unknown>((acc, key) => (acc && typeof acc === "object" ? (acc as Record<string, unknown>)[key] : undefined), obj);
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  try {
    return crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));
  } catch {
    return false;
  }
}

export function newReference(prefix = "CXIA-CE"): string {
  const ts = Date.now();
  const rand = crypto.randomBytes(2).toString("hex").toUpperCase();
  return `${prefix}-${ts}-${rand}`;
}
