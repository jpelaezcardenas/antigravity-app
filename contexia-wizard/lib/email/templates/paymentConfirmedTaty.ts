function formatCop(value: number): string {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 }).format(value);
}

export interface TatyEmailArgs {
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  razonSocial: string;
  tipoSociedad: string;
  ciudad?: string | null;
  reference: string;
  baseAmountCop: number;
  discountCop: number;
  finalAmountCop: number;
  couponCode?: string | null;
  paymentMethod: string;
  wompiTransactionId: string;
  accionistas?: Array<{ nombre: string; cedula?: string; participacion?: number }> | null;
  capital?: { total?: number; suscritoPct?: number; pagadoPct?: number } | null;
  representanteNombre?: string | null;
  descripcion?: string | null;
  ciiu?: string | null;
}

export function buildTatyNotificationEmail(args: TatyEmailArgs): { subject: string; html: string } {
  const subject = `💰 PAGO NUEVO: ${args.razonSocial} — ${formatCop(args.finalAmountCop)}`;
  const phoneDigits = (args.customerPhone || "").replace(/\D/g, "");
  const waPhone = phoneDigits.startsWith("57") ? phoneDigits : `57${phoneDigits}`;
  const waMsg = encodeURIComponent(
    `Hola ${(args.customerName || "").split(" ")[0]} 👋 Soy Taty de Contexia. Acabamos de recibir tu pago para crear *${args.razonSocial}* (orden ${args.reference}). Te contacto para confirmar los siguientes pasos del trámite.`
  );
  const waLink = `https://wa.me/${waPhone}?text=${waMsg}`;

  const accionistasRows = (args.accionistas || [])
    .map((a) => `<tr><td>${esc(a.nombre)}</td><td>${esc(a.cedula || "—")}</td><td style="text-align:right;">${a.participacion ?? "—"}%</td></tr>`)
    .join("");

  const html = `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>${subject}</title></head>
<body style="margin:0;padding:0;background:#0a2540;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0a2540;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a2540;padding:30px 20px;"><tr><td>
    <table width="640" cellpadding="0" cellspacing="0" style="margin:0 auto;background:#ffffff;border-radius:14px;max-width:640px;overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#2DD4BF,#8B5CF6);padding:20px 28px;color:#ffffff;">
        <h1 style="margin:0;font-size:18px;font-weight:800;">💰 Pago nuevo recibido</h1>
        <p style="margin:6px 0 0;font-size:13px;opacity:0.9;">Crear Empresa wizard · ${esc(args.reference)}</p>
      </td></tr>
      <tr><td style="padding:24px 28px;">
        <h2 style="margin:0 0 12px;font-size:20px;">${esc(args.razonSocial)} <span style="color:#64748b;font-weight:500;font-size:13px;">(${esc(args.tipoSociedad)})</span></h2>
        <div style="display:flex;gap:24px;flex-wrap:wrap;margin:0 0 20px;">
          <div><div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">Total cobrado</div><div style="font-size:22px;font-weight:800;color:#10b981;">${formatCop(args.finalAmountCop)}</div></div>
          ${args.discountCop > 0 ? `<div><div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">Cupón ${esc(args.couponCode || "")}</div><div style="font-size:15px;font-weight:700;color:#8B5CF6;">−${formatCop(args.discountCop)}</div></div>` : ""}
          <div><div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">Método</div><div style="font-size:15px;font-weight:700;">${esc(args.paymentMethod)}</div></div>
        </div>
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;">
          <h3 style="margin:0 0 10px;font-size:13px;color:#0a2540;">Contacto</h3>
          <p style="margin:0;font-size:14px;line-height:1.7;">
            <strong>${esc(args.customerName)}</strong><br/>
            📞 ${esc(args.customerPhone)}<br/>
            ✉️ <a href="mailto:${esc(args.customerEmail)}" style="color:#2563eb;">${esc(args.customerEmail)}</a><br/>
            ${args.ciudad ? `📍 ${esc(args.ciudad)}` : ""}
          </p>
        </div>

        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;">
          <h3 style="margin:0 0 10px;font-size:13px;color:#0a2540;">Empresa</h3>
          <p style="margin:0;font-size:14px;line-height:1.7;">
            ${args.descripcion ? `<strong>Actividad:</strong> ${esc(args.descripcion)}<br/>` : ""}
            ${args.ciiu ? `<strong>CIIU:</strong> ${esc(args.ciiu)}<br/>` : ""}
            ${args.capital?.total ? `<strong>Capital:</strong> ${formatCop(args.capital.total)} (${args.capital.suscritoPct ?? 100}% suscrito / ${args.capital.pagadoPct ?? 100}% pagado)<br/>` : ""}
            ${args.representanteNombre ? `<strong>Representante legal:</strong> ${esc(args.representanteNombre)}` : ""}
          </p>
        </div>

        ${accionistasRows ? `<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;">
          <h3 style="margin:0 0 10px;font-size:13px;color:#0a2540;">Accionistas</h3>
          <table width="100%" cellpadding="6" cellspacing="0" style="font-size:13px;">
            <thead><tr style="color:#64748b;text-align:left;"><th>Nombre</th><th>Cédula</th><th style="text-align:right;">%</th></tr></thead>
            <tbody>${accionistasRows}</tbody>
          </table>
        </div>` : ""}

        <div style="text-align:center;margin:24px 0 12px;">
          <a href="${waLink}" style="background:#25D366;color:#ffffff;text-decoration:none;font-weight:700;padding:14px 28px;border-radius:10px;display:inline-block;font-size:15px;">📲 Escribirle a ${esc((args.customerName || "").split(" ")[0])} por WhatsApp</a>
        </div>

        <p style="font-size:11px;color:#94a3b8;text-align:center;margin:16px 0 0;">
          Wompi TX: ${esc(args.wompiTransactionId)} · Ref: ${esc(args.reference)}
        </p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>`;
  return { subject, html };
}

function esc(s: string): string {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
