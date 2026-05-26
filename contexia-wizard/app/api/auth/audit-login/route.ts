import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

// POST /wizard/api/auth/audit-login
// Records every login attempt (success and failure). Called fire-and-forget from login.html.
// Frontend never reads from auth_audit — this endpoint only INSERTs via service_role.

const ALLOWED_OUTCOMES = new Set([
  "success",
  "invalid_credentials",
  "not_authorized",
  "unknown_email",
  "rate_limited",
  "error",
]);

const ALLOWED_METHODS = new Set(["password", "oauth_google", "oauth_microsoft"]);

const CORS_HEADERS = {
  // login.html is served from contexia.online (same registrable domain as the wizard proxy),
  // but during a deploy split the two can be on different Vercel projects. Allow same-site only.
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const outcome = String(body.outcome || "");
    const method = String(body.method || "");

    if (!ALLOWED_OUTCOMES.has(outcome) || !ALLOWED_METHODS.has(method)) {
      return NextResponse.json({ error: "invalid outcome or method" }, { status: 400, headers: CORS_HEADERS });
    }

    const ipHeader = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || "";
    const ip = ipHeader.split(",")[0]?.trim() || null;
    const userAgent = req.headers.get("user-agent") || null;

    const email = body.email ? String(body.email).toLowerCase().trim() : null;

    const { error } = await supabaseAdmin.from("auth_audit").insert({
      email,
      outcome,
      method,
      error_code: body.error_code ? String(body.error_code).slice(0, 64) : null,
      error_message: body.error_message ? String(body.error_message).slice(0, 500) : null,
      requested_role: body.requested_role ? String(body.requested_role).slice(0, 32) : null,
      resolved_role: body.resolved_role ? String(body.resolved_role).slice(0, 32) : null,
      destination: body.destination ? String(body.destination).slice(0, 256) : null,
      ip,
      user_agent: userAgent?.slice(0, 500) || null,
    });

    if (error) {
      console.error("auth_audit insert failed:", error);
      return NextResponse.json({ error: "insert failed" }, { status: 500, headers: CORS_HEADERS });
    }

    return NextResponse.json({ ok: true }, { status: 200, headers: CORS_HEADERS });
  } catch (err) {
    console.error("auth_audit handler error:", err);
    return NextResponse.json({ error: "bad request" }, { status: 400, headers: CORS_HEADERS });
  }
}
