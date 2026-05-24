/**
 * Tipos para Taty Contadora
 */

export type TatyChannel = "telegram" | "dashboard" | "whatsapp";

export interface TatyQuestion {
  text: string;
  company_id: string;
  channel: TatyChannel;
  timestamp: Date;
}

export interface TatyCitation {
  source: string;
  fragment: string;
}

export interface TatyAnswer {
  question: string;
  answer: string;
  citations: TatyCitation[];
  latency_ms: number;
  confidence: number;
  requires_human_review: boolean;
  timestamp: Date;
}

export type TatyUIStatus = "idle" | "loading" | "success" | "error";
