import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { paso1, leadId, source, feria_data } = body;

    if (!paso1?.email) {
      return NextResponse.json({ error: "Email requerido" }, { status: 400 });
    }

    const ip = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || null;
    const userAgent = req.headers.get("user-agent") || null;
    const referer = req.headers.get("referer") || null;

    // Build upsert payload
    const upsertData: Record<string, unknown> = {
      ...(leadId ? { id: leadId } : {}),
      nombre: paso1.nombre,
      cedula: paso1.cedula,
      email: paso1.email.toLowerCase().trim(),
      whatsapp: `${paso1.pais_codigo || ""}${paso1.whatsapp}`,
      ciudad: paso1.ciudad,
      rol: paso1.rol,
      ip_address: ip,
      user_agent: userAgent,
      referrer: referer,
      status: "contacted",
    };

    // Add feria source tag if present
    if (source) {
      upsertData.source = source;
    }

    // Store feria-specific fields in metadata JSONB (if column exists)
    if (feria_data) {
      upsertData.metadata = feria_data;
    }

    // Upsert lead by email (case-insensitive via unique index)
    const { data, error } = await supabaseAdmin
      .from("leads")
      .upsert(upsertData, { onConflict: "email", ignoreDuplicates: false })
      .select("id")
      .single();

    if (error) {
      console.error("Supabase upsert error:", error);
      // If error is about missing columns (source, metadata), try without them
      if (error.message?.includes("column") || error.code === "42703") {
        const fallbackData = { ...upsertData };
        delete fallbackData.source;
        delete fallbackData.metadata;
        const { data: fallbackResult, error: fallbackError } = await supabaseAdmin
          .from("leads")
          .upsert(fallbackData, { onConflict: "email", ignoreDuplicates: false })
          .select("id")
          .single();
        if (fallbackError) {
          return NextResponse.json({ error: fallbackError.message }, { status: 500 });
        }
        return NextResponse.json({ leadId: fallbackResult.id, fallback: true });
      }
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ leadId: data.id });
  } catch (err) {
    console.error("leads/save error:", err);
    return NextResponse.json({ error: "Error interno" }, { status: 500 });
  }
}
