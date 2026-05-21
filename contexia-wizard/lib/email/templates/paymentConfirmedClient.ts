function formatCop(value: number): string {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 }).format(value);
}

export interface ClientEmailArgs {
  customerName: string;
  customerEmail: string;
  razonSocial: string;
  reference: string;
  finalAmountCop: number;
  paymentMethod: string;
}

export function buildClientConfirmedEmail(args: ClientEmailArgs): { subject: string; html: string } {
  const firstName = (args.customerName || "").split(" ")[0] || "hola";
  const subject = `Recibimos tu pago — ${args.razonSocial}`;
  const html = `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>${subject}</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;"><tr><td>
    <table width="600" cellpadding="0" cellspacing="0" style="margin:0 auto;background:#ffffff;border-radius:16px;border:1px solid #e2e8f0;max-width:600px;overflow:hidden;">
      <tr><td style="background:#0a2540;padding:28px 36px;text-align:center;">
        <img src="https://www.contexia.online/assets/img/logo_official_transparent.png" alt="Contexia" height="44" style="display:block;margin:0 auto 16px;" />
        <h1 style="color:#ffffff;font-size:22px;font-weight:700;margin:0;">¡Pago confirmado!</h1>
        <p style="color:#2DD4BF;font-size:14px;margin:8px 0 0;">Empezamos a crear tu empresa</p>
      </td></tr>
      <tr><td style="padding:36px;">
        <p style="color:#1a202c;font-size:16px;margin:0 0 24px;">Hola <strong>${escapeHtml(firstName)}</strong>,</p>
        <p style="color:#475569;font-size:15px;line-height:1.7;margin:0 0 24px;">
          Recibimos tu pago de <strong>${formatCop(args.finalAmountCop)}</strong> por la constitución de <strong>${escapeHtml(args.razonSocial)}</strong>. Yo (Taty) te contacto en las próximas horas por WhatsApp para confirmar los siguientes pasos.
        </p>
        <div style="background:#f8fafc;border:2px solid #2DD4BF;border-radius:12px;padding:20px;margin-bottom:24px;">
          <table width="100%" cellpadding="6" cellspacing="0">
            <tr><td style="color:#64748b;font-size:13px;">Número de orden</td><td style="color:#0a2540;font-size:13px;font-weight:700;text-align:right;">${escapeHtml(args.reference)}</td></tr>
            <tr><td style="color:#64748b;font-size:13px;">Empresa</td><td style="color:#0a2540;font-size:13px;font-weight:700;text-align:right;">${escapeHtml(args.razonSocial)}</td></tr>
            <tr><td style="color:#64748b;font-size:13px;">Método de pago</td><td style="color:#0a2540;font-size:13px;font-weight:700;text-align:right;">${escapeHtml(args.paymentMethod)}</td></tr>
            <tr><td style="color:#64748b;font-size:13px;">Total</td><td style="color:#0a2540;font-size:15px;font-weight:800;text-align:right;">${formatCop(args.finalAmountCop)}</td></tr>
          </table>
        </div>
        <h3 style="color:#0a2540;font-size:16px;margin:24px 0 12px;">Qué sigue (5 días hábiles):</h3>
        <ol style="color:#475569;font-size:14px;line-height:1.8;padding-left:20px;margin:0 0 24px;">
          <li>Te llamo o escribo por WhatsApp para revisar los datos.</li>
          <li>Preparamos estatutos y los firmas digitalmente.</li>
          <li>Pagas Cámara de Comercio (~$50K-$400K según tu capital) — te ayudo a hacerlo desde tu cuenta.</li>
          <li>Radicamos en VUE y obtenemos NIT + RUT.</li>
          <li>¡Empresa lista, 100% digital!</li>
        </ol>
        <div style="text-align:center;margin:32px 0;">
          <a href="https://wa.me/573018948151?text=${encodeURIComponent(`Hola Taty, acabo de pagar mi empresa ${args.razonSocial}. Orden ${args.reference}.`)}" style="background:#25D366;color:#ffffff;text-decoration:none;font-weight:700;padding:14px 28px;border-radius:12px;display:inline-block;">💬 Escribir a Taty por WhatsApp</a>
        </div>
        <p style="color:#94a3b8;font-size:12px;text-align:center;margin:24px 0 0;">
          Guarda este correo. Si tienes dudas, responde aquí o escribe a <a href="mailto:growth@contexia.online" style="color:#2DD4BF;">growth@contexia.online</a>.
        </p>
      </td></tr>
      <tr><td style="background:#f1f5f9;padding:20px;text-align:center;color:#94a3b8;font-size:11px;">Contexia · Tu amiga contadora · contexia.online</td></tr>
    </table>
  </td></tr></table>
</body></html>`;
  return { subject, html };
}

function escapeHtml(s: string): string {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
