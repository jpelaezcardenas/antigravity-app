import { Resend } from "resend";
import { FROM_EMAIL, INTERNAL_NOTIFY_EMAILS } from "@/lib/notifications";
import { buildClientConfirmedEmail, type ClientEmailArgs } from "./templates/paymentConfirmedClient";
import { buildTatyNotificationEmail, type TatyEmailArgs } from "./templates/paymentConfirmedTaty";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function sendPaymentConfirmation(args: {
  client: ClientEmailArgs;
  taty: TatyEmailArgs;
}): Promise<{ clientId?: string; tatyId?: string; errors?: string[] }> {
  const errors: string[] = [];
  let clientId: string | undefined;
  let tatyId: string | undefined;

  const client = buildClientConfirmedEmail(args.client);
  const taty = buildTatyNotificationEmail(args.taty);

  try {
    const r1 = await resend.emails.send({
      from: FROM_EMAIL,
      to: args.client.customerEmail,
      subject: client.subject,
      html: client.html,
    });
    if (r1.error) errors.push(`client: ${r1.error.message}`);
    else clientId = r1.data?.id;
  } catch (e) {
    errors.push(`client exception: ${(e as Error).message}`);
  }

  try {
    const r2 = await resend.emails.send({
      from: FROM_EMAIL,
      to: INTERNAL_NOTIFY_EMAILS,
      subject: taty.subject,
      html: taty.html,
    });
    if (r2.error) errors.push(`taty: ${r2.error.message}`);
    else tatyId = r2.data?.id;
  } catch (e) {
    errors.push(`taty exception: ${(e as Error).message}`);
  }

  return { clientId, tatyId, errors: errors.length ? errors : undefined };
}
