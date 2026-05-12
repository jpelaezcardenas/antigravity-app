import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";
import { supabaseAdmin } from "@/lib/supabase";

const FROM_EMAIL = "Taty de Contexia <growth@contexia.online>";
const NOTIFY_EMAILS = ["jpelaezcardenas@gmail.com", "tatybarbosav91@gmail.com"];

const resend = new Resend(process.env.RESEND_API_KEY);

function escape(s: string): string {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] || c)
  );
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Cal.com webhook payload: { triggerEvent, payload: { ... } }
    const event = body?.triggerEvent || "UNKNOWN";
    const p = body?.payload || {};

    if (event !== "BOOKING_CREATED" && event !== "BOOKING_RESCHEDULED" && event !== "BOOKING_CANCELLED") {
      return NextResponse.json({ ok: true, ignored: event });
    }

    const attendeeName = p.attendees?.[0]?.name || p.responses?.name?.value || "Invitado";
    const attendeeEmail = p.attendees?.[0]?.email || p.responses?.email?.value || "—";
    const title = p.title || p.eventType?.title || "Reunión";
    const startTime = p.startTime || p.responses?.startTime?.value || "";
    const endTime = p.endTime || "";
    const meetingUrl = p.metadata?.videoCallUrl || p.location || p.additionalNotes || "";
    const cancelUrl = p.cancelUrl || `https://cal.com/booking/${p.uid || ""}`;
    const rescheduleUrl = p.rescheduleUrl || "";
    const eventColor = event === "BOOKING_CANCELLED" ? "#dc2626" : event === "BOOKING_RESCHEDULED" ? "#f59e0b" : "#16a34a";
    const eventLabel =
      event === "BOOKING_CANCELLED" ? "❌ Booking cancelado"
      : event === "BOOKING_RESCHEDULED" ? "🔄 Booking reagendado"
      : "✅ Nuevo agendamiento";

    let fechaLegible = "";
    try {
      if (startTime) {
        fechaLegible = new Date(startTime).toLocaleString("es-CO", {
          weekday: "long", year: "numeric", month: "long", day: "numeric",
          hour: "2-digit", minute: "2-digit", timeZone: "America/Bogota",
        });
      }
    } catch { /* ignore */ }

    const html = `<!DOCTYPE html>
<html lang="es">
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
    <tr><td>
      <table width="600" cellpadding="0" cellspacing="0" style="margin:0 auto;background:#fff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;max-width:600px;">
        <tr><td style="background:${eventColor};padding:24px 32px;color:#fff;">
          <div style="font-size:13px;font-weight:600;letter-spacing:0.05em;opacity:0.9;text-transform:uppercase;">${eventLabel}</div>
          <h1 style="margin:8px 0 0;font-size:22px;font-weight:800;">${escape(title)}</h1>
        </td></tr>
        <tr><td style="padding:28px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="padding:10px 0;color:#64748b;font-size:13px;width:130px;">👤 Invitado</td>
                <td style="padding:10px 0;font-weight:700;color:#0a2540;">${escape(attendeeName)}</td></tr>
            <tr><td style="padding:10px 0;color:#64748b;font-size:13px;">📧 Email</td>
                <td style="padding:10px 0;font-weight:700;"><a href="mailto:${escape(attendeeEmail)}" style="color:#0a2540;">${escape(attendeeEmail)}</a></td></tr>
            ${fechaLegible ? `<tr><td style="padding:10px 0;color:#64748b;font-size:13px;">📅 Fecha y hora</td>
                <td style="padding:10px 0;font-weight:700;color:#0a2540;">${escape(fechaLegible)}</td></tr>` : ""}
            ${meetingUrl ? `<tr><td style="padding:10px 0;color:#64748b;font-size:13px;">🎥 Link reunión</td>
                <td style="padding:10px 0;"><a href="${escape(meetingUrl)}" style="color:#0a8d63;font-weight:700;word-break:break-all;">${escape(meetingUrl)}</a></td></tr>` : ""}
          </table>
          <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;">
            ${meetingUrl ? `<a href="${escape(meetingUrl)}" style="display:inline-block;background:#0a8d63;color:#fff;font-weight:700;padding:12px 24px;border-radius:10px;text-decoration:none;font-size:14px;margin:4px;">🎥 Unirse a la reunión</a>` : ""}
            ${rescheduleUrl ? `<a href="${escape(rescheduleUrl)}" style="display:inline-block;background:#0a2540;color:#fff;font-weight:700;padding:12px 24px;border-radius:10px;text-decoration:none;font-size:14px;margin:4px;">🔄 Reagendar</a>` : ""}
          </div>
          <p style="color:#94a3b8;font-size:11px;margin:24px 0 0;border-top:1px solid #e2e8f0;padding-top:16px;">
            Webhook recibido desde Cal.com · Contexia Shadow Audit
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;

    await resend.emails.send({
      from: FROM_EMAIL,
      to: NOTIFY_EMAILS,
      subject: `${eventLabel}: ${attendeeName} — ${title}`,
      html,
    });

    // Persist booking event in Supabase (non-blocking, table optional)
    try {
      await supabaseAdmin.from("cal_bookings").insert({
        event_type: event,
        attendee_name: attendeeName,
        attendee_email: attendeeEmail,
        title,
        start_time: startTime || null,
        end_time: endTime || null,
        meeting_url: meetingUrl || null,
        raw_payload: body,
      });
    } catch (dbErr) {
      console.error("cal_bookings insert error (non-blocking):", dbErr);
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("cal webhook error:", err);
    return NextResponse.json({ error: "Error procesando webhook" }, { status: 500 });
  }
}
