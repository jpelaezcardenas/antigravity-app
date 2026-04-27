import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { leadId, result, paso1 } = body;

    if (!result) {
      return NextResponse.json({ error: "Resultado de auditoría requerido" }, { status: 400 });
    }

    // If we have a leadId, update the existing row
    if (leadId) {
      await supabaseAdmin
        .from("leads")
        .update({
          audit_result: result,
          audit_executed_at: new Date().toISOString(),
          status: "audited",
          lead_score: result.readinessScore || 0,
        })
        .eq("id", leadId);
    } else if (paso1?.email) {
      // Fallback: update by email
      await supabaseAdmin
        .from("leads")
        .update({
          audit_result: result,
          audit_executed_at: new Date().toISOString(),
          status: "audited",
          lead_score: result.readinessScore || 0,
        })
        .eq("email", paso1.email.toLowerCase().trim());
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("audit/execute error:", err);
    return NextResponse.json({ error: "Error interno" }, { status: 500 });
  }
}
