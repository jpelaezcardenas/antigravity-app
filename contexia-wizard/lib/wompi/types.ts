export type WompiTransactionStatus =
  | "PENDING"
  | "APPROVED"
  | "DECLINED"
  | "VOIDED"
  | "ERROR";

export type PaymentMethodType =
  | "CARD"
  | "PSE"
  | "NEQUI"
  | "BANCOLOMBIA_TRANSFER"
  | "BANCOLOMBIA_COLLECT"
  | "DAVIPLATA"
  | "BANCOLOMBIA_BUTTON";

export interface WompiTransaction {
  id: string;
  amount_in_cents: number;
  reference: string;
  customer_email: string;
  currency: string;
  payment_method_type: PaymentMethodType;
  status: WompiTransactionStatus;
  status_message?: string | null;
  created_at: string;
  finalized_at?: string | null;
}

export interface WompiEventSignature {
  properties: string[];
  checksum: string;
}

export interface WompiWebhookEvent {
  event: "transaction.updated";
  data: { transaction: WompiTransaction };
  sent_at: string;
  timestamp: number;
  signature: WompiEventSignature;
  environment: "test" | "prod";
}
