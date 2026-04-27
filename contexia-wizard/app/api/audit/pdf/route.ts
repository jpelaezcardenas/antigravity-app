import { NextRequest, NextResponse } from "next/server";
import { renderToBuffer } from "@react-pdf/renderer";
import React from "react";
import { DiagnosticoPDF } from "@/pdf/DiagnosticoPDF";
import { supabaseAdmin } from "@/lib/supabase";

// ─── Route Handler ────────────────────────────────────────────
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const email = searchParams.get("email") || "";
    const leadId = searchParams.get("leadId") || "";

    // Fetch lead data from Supabase
    let result: any = null;
    let nombre = "Empresario";
    let empresa = "Tu empresa";

    if (email || leadId) {
      const query = supabaseAdmin
        .from("leads")
        .select("audit_result, nombre, email, empresa");

      if (leadId) {
        query.eq("id", leadId);
      } else {
        query.eq("email", email.toLowerCase().trim());
      }

      const { data } = await query.single();
      if (data) {
        result = data.audit_result;
        nombre = data.nombre || "Empresario";
        empresa = data.empresa || "Tu empresa";
      }
    }

    if (!result) {
      return NextResponse.json(
        { error: "No se encontró el resultado del audit" },
        { status: 404 }
      );
    }

    // Generate PDF buffer using @react-pdf/renderer
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const buffer = await renderToBuffer(
      React.createElement(DiagnosticoPDF, { result, nombre, empresa }) as any
    );

    // Mark as downloaded in Supabase
    if (leadId || email) {
      const updateQuery = supabaseAdmin
        .from("leads")
        .update({ diagnostic_downloaded: true });
      if (leadId) {
        updateQuery.eq("id", leadId);
      } else {
        updateQuery.eq("email", email.toLowerCase().trim());
      }
      await updateQuery;
    }

    return new NextResponse(buffer as unknown as BodyInit, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="shadow-audit-contexia.pdf"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (err) {
    console.error("audit/pdf error:", err);
    return NextResponse.json(
      { error: "Error generando PDF" },
      { status: 500 }
    );
  }
}
