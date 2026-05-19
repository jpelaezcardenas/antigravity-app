import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";
import { supabaseAdmin } from "@/lib/supabase";
import { INTERNAL_NOTIFY_EMAILS, FROM_EMAIL, CAL_BOOKING_URL } from "@/lib/notifications";

const resend = new Resend(process.env.RESEND_API_KEY);

function formatCOP(value: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { leadId, result, paso1, paso2 } = body;

    if (!result) {
      return NextResponse.json({ error: "Resultado de auditoría requerido" }, { status: 400 });
    }

    // Persist audit_result in Supabase — UPSERT para que el flujo con prefill
    // (que salta /api/leads/save) también cree el registro.
    let resolvedLeadId: string | null = leadId || null;

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
      const normalizedEmail = paso1.email.toLowerCase().trim();
      // Verificar si el lead ya existe
      const { data: existing } = await supabaseAdmin
        .from("leads")
        .select("id")
        .eq("email", normalizedEmail)
        .maybeSingle();

      if (existing) {
        resolvedLeadId = existing.id;
        await supabaseAdmin
          .from("leads")
          .update({
            audit_result: result,
            audit_executed_at: new Date().toISOString(),
            status: "audited",
            lead_score: result.readinessScore || 0,
          })
          .eq("id", existing.id);
      } else {
        // Insertar nuevo lead con info del paso 1 + audit result (caso del prefill)
        const ip = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || null;
        const userAgent = req.headers.get("user-agent") || null;
        const referer = req.headers.get("referer") || null;
        const { data: inserted } = await supabaseAdmin
          .from("leads")
          .insert({
            nombre: paso1.nombre || null,
            cedula: paso1.cedula || null,
            email: normalizedEmail,
            whatsapp: `${paso1.pais_codigo || ""}${paso1.whatsapp || ""}` || null,
            ciudad: paso1.ciudad || null,
            rol: paso1.rol || null,
            audit_result: result,
            audit_executed_at: new Date().toISOString(),
            status: "audited",
            lead_score: result.readinessScore || 0,
            ip_address: ip,
            user_agent: userAgent,
            referrer: referer,
          })
          .select("id")
          .single();
        resolvedLeadId = inserted?.id || null;
      }
    }

    // ── Dispara alerta interna al equipo Contexia ─────────────
    try {
      const nombre = paso1?.nombre || "Lead sin nombre";
      const email = paso1?.email || "—";
      const whatsapp = paso1?.whatsapp || "";
      const ciudad = paso1?.ciudad || "";
      const rol = paso1?.rol || "";
      const empresa = paso2?.nombre_opcion1 || "Empresa sin nombre";
      const sector = paso2?.sector || "";
      const ciiu = paso2?.ciiu_principal || "";

      const ahorroStr = formatCOP(result.ahorroPotencial || 0);
      const scoreStr = result.readinessScore ?? "N/A";
      const scoreBand = String(result.readinessBand || "").toLowerCase();
      const scoreColor = scoreBand === "verde" ? "#16a34a" : scoreBand === "ambar" ? "#f59e0b" : "#dc2626";
      const regimenLabel = result.recomendacion === "simple" ? "Régimen Simple" : "Régimen Ordinario";
      const regimenColor = result.recomendacion === "simple" ? "#16a34a" : "#2563eb";
      const riesgosCount = (result.riesgos || []).length;
      const oportunidadesCount = (result.oportunidades || []).length;

      // Clasificación de temperatura del lead por ahorro potencial
      const heatLabel = result.ahorroPotencial > 50000000
        ? "🔥 CALIENTE"
        : result.ahorroPotencial > 10000000
        ? "🌡️ TIBIO"
        : "❄️ FRÍO";

      const waDigits = String(whatsapp).replace(/\D/g, "");
      const waE164 = waDigits ? `57${waDigits}` : "";
      const waMessage = encodeURIComponent(
        `Hola ${nombre.split(" ")[0]}, vi tu Shadow Audit de ${empresa}. ¿Agendamos 30 min para revisarlo juntos? ${CAL_BOOKING_URL}`
      );

      // Top 3 riesgos para mostrar en email
      const topRiesgos = (result.riesgos || []).slice(0, 3).map((r: any) => `
        <tr><td style="padding:6px 0;">
          <span style="display:inline-block;background:${r.nivel === "CRÍTICO" ? "#fef2f2" : r.nivel === "ALTO" ? "#fffbeb" : "#eff6ff"};color:${r.nivel === "CRÍTICO" ? "#dc2626" : r.nivel === "ALTO" ? "#d97706" : "#2563eb"};font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;margin-right:8px;">${r.nivel}</span>
          <span style="font-size:13px;color:#0a2540;">${r.titulo || ""}</span>
        </td></tr>
      `).join("");

      await resend.emails.send({
        from: FROM_EMAIL,
        to: INTERNAL_NOTIFY_EMAILS,
        subject: `${heatLabel} Nuevo Lead: ${nombre} — ${empresa} · ${ahorroStr}/año ahorro`,
        html: `<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
          <div style="max-width:580px;margin:32px auto;background:#fff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;">
            <div style="background:#0a2540;padding:22px 28px;color:#fff;">
              <div style="font-size:12px;font-weight:600;opacity:0.85;letter-spacing:0.05em;text-transform:uppercase;">${heatLabel} · Shadow Audit Completado</div>
              <h2 style="margin:6px 0 0;font-size:20px;font-weight:800;line-height:1.3;">${nombre}</h2>
              <p style="margin:4px 0 0;color:#94a3b8;font-size:14px;">${empresa}${rol ? ` · ${rol}` : ""}${ciudad ? ` · ${ciudad}` : ""}</p>
              ${sector ? `<p style="margin:6px 0 0;color:#94a3b8;font-size:12px;font-style:italic;">${sector}${ciiu ? ` (CIIU ${ciiu})` : ""}</p>` : ""}
            </div>
            <div style="padding:24px 28px;">

              <!-- Contacto -->
              <h3 style="color:#0a2540;font-size:13px;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:0.05em;">📇 Contacto</h3>
              <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
                <tr><td style="padding:6px 0;color:#64748b;font-size:13px;width:120px;">Email</td><td style="padding:6px 0;font-weight:700;"><a href="mailto:${email}" style="color:#0a8d63;">${email}</a></td></tr>
                ${whatsapp ? `<tr><td style="padding:6px 0;color:#64748b;font-size:13px;">WhatsApp</td><td style="padding:6px 0;font-weight:700;"><a href="https://wa.me/${waE164}" style="color:#25d366;">+57 ${whatsapp}</a></td></tr>` : ""}
              </table>

              <!-- Resultados del audit -->
              <h3 style="color:#0a2540;font-size:13px;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:0.05em;">📊 Resultados</h3>
              <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
                <tr><td style="padding:6px 0;color:#64748b;font-size:13px;width:120px;">Régimen</td><td style="padding:6px 0;font-weight:700;color:${regimenColor};">${regimenLabel}</td></tr>
                <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Ahorro/año</td><td style="padding:6px 0;font-weight:800;color:#16a34a;font-size:16px;">${ahorroStr}</td></tr>
                <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Readiness</td><td style="padding:6px 0;font-weight:700;color:${scoreColor};">${scoreStr}/100 · ${scoreBand.toUpperCase() || "—"}</td></tr>
                <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Riesgos</td><td style="padding:6px 0;font-weight:700;color:#dc2626;">${riesgosCount} identificados</td></tr>
                <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Oportunidades</td><td style="padding:6px 0;font-weight:700;color:#0a8d63;">${oportunidadesCount}</td></tr>
              </table>

              ${topRiesgos ? `
              <h3 style="color:#0a2540;font-size:13px;font-weight:700;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.05em;">⚠️ Top riesgos</h3>
              <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">${topRiesgos}</table>
              ` : ""}

              <!-- Acciones rápidas -->
              <div style="padding:18px;background:#f0fdf4;border-radius:12px;text-align:center;margin-top:8px;">
                <p style="margin:0 0 12px;color:#0a2540;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">⚡ Acción inmediata</p>
                ${waE164 ? `<a href="https://wa.me/${waE164}?text=${waMessage}" style="display:inline-block;background:#25d366;color:#fff;font-weight:700;padding:11px 22px;border-radius:8px;text-decoration:none;font-size:13px;margin:4px;">💬 Escribir por WhatsApp</a>` : ""}
                <a href="${CAL_BOOKING_URL}" style="display:inline-block;background:#0a2540;color:#fff;font-weight:700;padding:11px 22px;border-radius:8px;text-decoration:none;font-size:13px;margin:4px;">📅 Mi agenda Cal.com</a>
              </div>

              <p style="color:#94a3b8;font-size:11px;margin:20px 0 0;border-top:1px solid #e2e8f0;padding-top:14px;">
                Contexia · Shadow Audit · ${new Date().toLocaleString("es-CO", { timeZone: "America/Bogota" })}
              </p>
            </div>
          </div>
        </body></html>`,
      });
    } catch (notifyErr) {
      console.error("Internal alert error (non-blocking):", notifyErr);
    }

    return NextResponse.json({ ok: true, leadId: resolvedLeadId });
  } catch (err) {
    console.error("audit/execute error:", err);
    return NextResponse.json({ error: "Error interno" }, { status: 500 });
  }
}
