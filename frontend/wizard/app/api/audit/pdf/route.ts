import { NextRequest, NextResponse } from "next/server";
import { renderToBuffer } from "@react-pdf/renderer";
import React from "react";
import { DiagnosticoPDF } from "@/pdf/DiagnosticoPDF";
import { supabaseAdmin } from "@/lib/supabase";

// ─── Route Handler ────────────────────────────────────────────
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const email = (searchParams.get("email") || "").trim();
    const leadId = (searchParams.get("leadId") || "").trim();

    // Fetch lead data from Supabase
    let result: any = null;
    let nombre = "Empresario";
    let empresa = "Tu empresa";

    if (email || leadId) {
      // Columns that actually exist in the leads table — no `empresa` directly,
      // but we can read paso2.nombre_opcion1 from the audit_result or full row
      let query = supabaseAdmin
        .from("leads")
        .select("audit_result, nombre, email")
        .limit(1);

      if (leadId) {
        query = query.eq("id", leadId);
      } else if (email) {
        query = query.eq("email", email.toLowerCase());
      }

      const { data, error } = await query.maybeSingle();
      if (error) {
        console.error("PDF lookup error:", error);
      }
      if (data) {
        result = data.audit_result;
        nombre = data.nombre || "Empresario";
        // Empresa vive dentro del audit_result o pasos guardados; fallback al default
        const r: any = result;
        empresa = r?.empresa || r?.paso2?.nombre_opcion1 || "Tu empresa";
      }
    }

    if (!result) {
      return NextResponse.json(
        {
          error: "No se encontró el resultado del audit",
          hint: "Asegúrate de haber ejecutado el Shadow Audit antes de descargar el PDF. Si usaste el modo prefill, primero pulsa 'Ejecutar Shadow Audit' en el paso 8.",
          email,
          leadId,
        },
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
        updateQuery.eq("email", email.toLowerCase());
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
  } catch (err: any) {
    console.error("audit/pdf error:", err);
    return NextResponse.json(
      { error: "Error generando PDF", detail: err?.message || String(err) },
      { status: 500 }
    );
  }
}
