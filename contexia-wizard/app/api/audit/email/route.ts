import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";
import { supabaseAdmin } from "@/lib/supabase";

// Email sender confirmed: growth@contexia.online
const FROM_EMAIL = "Taty de Contexia <growth@contexia.online>";

const resend = new Resend(process.env.RESEND_API_KEY);

function formatCOP(value: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function buildEmailHtml(nombre: string, result: any): string {
  const primerNombre = nombre.split(" ")[0];
  const regimen = result.recomendacion === "simple" ? "Régimen Simple" : "Régimen Ordinario";
  const regimenColor = result.recomendacion === "simple" ? "#16a34a" : "#2563eb";
  const ahorroStr = formatCOP(result.ahorroPotencial);
  const impuestoStr = result.recomendacion === "simple"
    ? formatCOP(result.impuestoSimple)
    : formatCOP(result.impuestoOrdinario);

  const riesgosCriticos = (result.riesgos || []).filter((r: any) => r.nivel === "CRÍTICO" || r.nivel === "ALTO");
  const riesgosHtml = riesgosCriticos.slice(0, 3).map((r: any) => `
    <tr>
      <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
        <span style="display:inline-block;background:${r.nivel === "CRÍTICO" ? "#fef2f2" : "#fffbeb"};color:${r.nivel === "CRÍTICO" ? "#dc2626" : "#d97706"};font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;margin-right:8px;">${r.nivel}</span>
        <strong style="color:#1a202c;">${r.titulo}</strong>
      </td>
    </tr>
  `).join("");

  return `<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Tu Shadow Audit — Contexia</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
    <tr><td>
      <table width="600" cellpadding="0" cellspacing="0" style="margin:0 auto;background:#ffffff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;max-width:600px;">
        
        <!-- Header -->
        <tr><td style="background:#0a2540;padding:28px 36px;text-align:center;">
          <img src="https://www.contexia.online/assets/img/logo_official_transparent.png" alt="Contexia" height="44" style="display:block;margin:0 auto 16px;" />
          <h1 style="color:#ffffff;font-size:22px;font-weight:700;margin:0 0 8px;">Tu Shadow Audit está listo</h1>
          <p style="color:#94a3b8;font-size:14px;margin:0;">Diagnóstico tributario personalizado</p>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:36px;">
          <p style="color:#1a202c;font-size:16px;margin:0 0 24px;">Hola <strong>${primerNombre}</strong>,</p>
          <p style="color:#475569;font-size:15px;line-height:1.7;margin:0 0 24px;">
            Completé el análisis de tu empresa y aquí tienes los resultados clave de tu <strong>Shadow Audit</strong>:
          </p>

          <!-- Veredicto principal -->
          <div style="background:#f8fafc;border-radius:12px;border:2px solid ${regimenColor};padding:24px;text-align:center;margin-bottom:24px;">
            <div style="font-size:13px;color:#64748b;margin-bottom:8px;">RÉGIMEN RECOMENDADO</div>
            <div style="font-size:26px;font-weight:800;color:${regimenColor};margin-bottom:8px;">${regimen}</div>
            <div style="font-size:28px;font-weight:700;color:#0a2540;">${impuestoStr}/año</div>
            ${result.ahorroPotencial > 0 ? `<div style="margin-top:12px;background:#f0fdf4;border-radius:8px;padding:10px;color:#16a34a;font-weight:700;font-size:15px;">💰 Ahorro potencial: ${ahorroStr}/año</div>` : ""}
          </div>

          <!-- Métricas -->
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
            <tr>
              <td style="width:33%;text-align:center;background:#f8fafc;border-radius:10px;padding:16px;border:1px solid #e2e8f0;">
                <div style="font-size:20px;font-weight:700;color:#1a202c;">${result.readinessScore}/100</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">Readiness Score</div>
              </td>
              <td style="width:4%;"></td>
              <td style="width:30%;text-align:center;background:#f8fafc;border-radius:10px;padding:16px;border:1px solid #e2e8f0;">
                <div style="font-size:20px;font-weight:700;color:#dc2626;">${riesgosCriticos.length}</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">Riesgos Críticos/Altos</div>
              </td>
              <td style="width:4%;"></td>
              <td style="width:30%;text-align:center;background:#f8fafc;border-radius:10px;padding:16px;border:1px solid #e2e8f0;">
                <div style="font-size:20px;font-weight:700;color:#16a34a;">${(result.oportunidades || []).length}</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">Oportunidades</div>
              </td>
            </tr>
          </table>

          <!-- Riesgos top -->
          ${riesgosHtml ? `
          <h3 style="color:#0a2540;font-size:16px;margin:0 0 12px;">Riesgos prioritarios a atender:</h3>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">${riesgosHtml}</table>
          ` : ""}

          <!-- CTA Principal -->
          <div style="text-align:center;margin:32px 0;">
            <a href="https://www.contexia.online/crear-empresa.html"
               style="display:inline-block;background:#00a878;color:#ffffff;font-weight:700;font-size:16px;padding:16px 40px;border-radius:12px;text-decoration:none;">
              Formalizar mi empresa — $1.200.000 COP
            </a>
          </div>

          <!-- Secondary CTA -->
          <div style="text-align:center;margin-bottom:32px;">
            <a href="https://wa.me/573018948151?text=Hola%20Taty,%20recibí%20mi%20Shadow%20Audit%20y%20quiero%20hablar%20con%20un%20experto"
               style="display:inline-block;background:#0a2540;color:#ffffff;font-weight:600;font-size:14px;padding:12px 28px;border-radius:10px;text-decoration:none;">
              💬 Hablar con experto por WhatsApp
            </a>
          </div>

          <!-- Disclaimer -->
          <p style="color:#94a3b8;font-size:12px;line-height:1.7;border-top:1px solid #e2e8f0;padding-top:20px;margin-top:20px;">
            <strong>Disclaimer:</strong> Este análisis es una herramienta de orientación automática. No constituye asesoría legal, contable o tributaria formal. Las cifras son estimaciones basadas en normativa vigente y pueden variar al validar con tus números reales.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f8fafc;padding:20px 36px;text-align:center;border-top:1px solid #e2e8f0;">
          <p style="color:#94a3b8;font-size:12px;margin:0;">
            © 2026 Contexia SAS · growth@contexia.online · Medellín, Colombia<br/>
            <a href="https://www.contexia.online/landing" style="color:#00a878;">contexia.online</a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, leadId, result, nombre } = body;

    if (!email || !result) {
      return NextResponse.json({ error: "Email y resultado son requeridos" }, { status: 400 });
    }

    const html = buildEmailHtml(nombre || "Empresario", result);
    const regimenLabel = result.recomendacion === "simple" ? "Régimen Simple" : "Régimen Ordinario";

    const { data, error } = await resend.emails.send({
      from: FROM_EMAIL,
      to: [email],
      subject: `Tu Shadow Audit: ${regimenLabel} es tu mejor opción — Contexia`,
      html,
    });

    if (error) {
      console.error("Resend error:", error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // Mark as emailed in Supabase
    if (leadId) {
      await supabaseAdmin
        .from("leads")
        .update({ diagnostic_emailed: true, status: "emailed" })
        .eq("id", leadId);
    }

    return NextResponse.json({ ok: true, messageId: data?.id });
  } catch (err) {
    console.error("audit/email error:", err);
    return NextResponse.json({ error: "Error interno" }, { status: 500 });
  }
}
