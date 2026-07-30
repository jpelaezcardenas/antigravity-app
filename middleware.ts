// Vercel Edge Middleware — gates /app/* behind a valid Supabase JWT
// stored in the `sb-access-token` cookie. Verifies HS256 signature with Web Crypto API
// (no npm deps). Role-aware: /app-admin/* requires role=admin.
// Redirects unknown /app/* paths to role-appropriate defaults.
//
// Requires Vercel env var: SUPABASE_JWT_SECRET (Supabase Dashboard → Settings → API → JWT Secret).

import type { NextRequest } from "next/server";

export const config = {
  matcher: ["/((?!_next/|wizard/|favicon|assets/|.*\\.(?:css|js|png|jpg|jpeg|svg|gif|ico|woff2?|ttf)$).*)"],
};

const PUBLIC_PATHS = new Set([
  "/",
  "/landing.html",
  "/login.html",
  "/reset-password.html",
  "/logout.html",
  "/index.html",
  "/404.html",
  "/_not-found.html",
  "/crear-empresa",
  "/crear-empresa.html",
  "/crear-empresa-wizard",
  "/crear-empresa-wizard.html",
]);

const PUBLIC_PREFIXES = ["/wizard", "/_next", "/assets", "/app/dashboard-assets", "/app/assets"];

const ADMIN_ONLY = ["/app-admin"];

const KNOWN_APP_PATHS = new Set([
  "/app/overview",
  "/app/fiscal",
  "/app/radar",
  "/app/patrimonio",
  "/app/config",
  "/app/flujo-detalle",
  "/app/bunker",
]);

const APP_ASSET_PREFIXES = ["/app/dashboard-assets", "/app/assets"];

function base64UrlDecode(str: string): Uint8Array {
  const pad = str.length % 4 === 0 ? "" : "=".repeat(4 - (str.length % 4));
  const b64 = (str + pad).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function toUtf8(bytes: Uint8Array): string {
  return new TextDecoder().decode(bytes);
}

async function verifyJwt(token: string, secret: string): Promise<Record<string, unknown> | null> {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, signatureB64] = parts;

  try {
    const header = JSON.parse(toUtf8(base64UrlDecode(headerB64))) as { alg?: string };
    if (header.alg !== "HS256") return null;

    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["verify"],
    );

    const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const signature = base64UrlDecode(signatureB64);
    const ok = await crypto.subtle.verify("HMAC", key, signature, data);
    if (!ok) return null;

    const payload = JSON.parse(toUtf8(base64UrlDecode(payloadB64))) as Record<string, unknown>;
    const exp = typeof payload.exp === "number" ? payload.exp : 0;
    if (Date.now() / 1000 >= exp) return null;
    return payload;
  } catch {
    return null;
  }
}

function extractRole(payload: Record<string, unknown>): string {
  const appMeta = (payload.app_metadata as Record<string, unknown> | undefined) || {};
  const userMeta = (payload.user_metadata as Record<string, unknown> | undefined) || {};
  const raw =
    (appMeta.role as string | undefined) ||
    (appMeta.account_role as string | undefined) ||
    (userMeta.role as string | undefined) ||
    (userMeta.account_role as string | undefined) ||
    "";
  return String(raw).toLowerCase();
}

function isAdmin(role: string, payload: Record<string, unknown>): boolean {
  if (["admin", "superadmin", "contexia_admin"].includes(role)) return true;
  const appMeta = (payload.app_metadata as Record<string, unknown> | undefined) || {};
  const userMeta = (payload.user_metadata as Record<string, unknown> | undefined) || {};
  const roles = (appMeta.roles as unknown[] | undefined) || (userMeta.roles as unknown[] | undefined);
  return Array.isArray(roles) && roles.some((r) => String(r).toLowerCase() === "admin");
}

function isPublic(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  return PUBLIC_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(prefix + "/"));
}

function needsAdmin(pathname: string): boolean {
  return ADMIN_ONLY.some((prefix) => pathname === prefix || pathname.startsWith(prefix + "/"));
}

function isAppAsset(pathname: string): boolean {
  return APP_ASSET_PREFIXES.some((prefix) => pathname.startsWith(prefix + "/"));
}

export async function middleware(req: NextRequest) {
  const { pathname, search } = new URL(req.url);

  if (isPublic(pathname)) return;

  const token = req.cookies.get("sb-access-token")?.value;
  const secret = process.env.SUPABASE_JWT_SECRET;

  const loginUrl = new URL("/login.html", req.url);
  loginUrl.searchParams.set("next", pathname + search);

  if (!secret) {
    console.error("[middleware] SUPABASE_JWT_SECRET not set — failing closed for", pathname);
    return Response.redirect(loginUrl, 302);
  }

  if (!token) {
    return Response.redirect(loginUrl, 302);
  }

  const payload = await verifyJwt(token, secret);
  if (!payload) {
    return Response.redirect(loginUrl, 302);
  }

  if (needsAdmin(pathname)) {
    const role = extractRole(payload);
    if (!isAdmin(role, payload)) {
      return Response.redirect(new URL("/app/overview", req.url), 302);
    }
  }

  // /app exact → redirect to /app/bunker (shared surface, role filtering happens client-side)
  if (pathname === "/app") {
    return Response.redirect(new URL("/app/bunker", req.url), 302);
  }

  // Unknown /app/* paths → redirect to role-appropriate default
  if (pathname.startsWith("/app/") && !KNOWN_APP_PATHS.has(pathname) && !isAppAsset(pathname)) {
    const role = extractRole(payload);
    const dest = isAdmin(role, payload) ? "/app/bunker" : "/app/overview";
    return Response.redirect(new URL(dest, req.url), 302);
  }

  return;
}
