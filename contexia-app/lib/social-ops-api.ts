/**
 * Social Content Ops API client — the second data-bound exception to
 * contexia-app's mock-first rule, alongside CashTodayCard (see CLAUDE.md
 * "Pantallas data-bound"). Calls the canonical `/api/v1/social-ops/*`
 * backend on Railway (same origin as lib/api-client.ts).
 */

import { API_BASE_URL } from "./config";
import { authenticatedFetch } from "./authenticated-fetch";

export type SocialChannel = "telegram" | "facebook" | "instagram" | "tiktok" | "linkedin";

export interface SocialLead {
  id: string;
  primary_channel: SocialChannel;
  actor_handle: string;
  display_name: string;
  maturity_stage: string;
  pipeline_stage: string;
  urgency: "low" | "medium" | "high" | "critical";
  pain_tags: string[];
  score: number;
  last_message: string;
  last_event_at: string;
}

export interface SocialOpsEvent {
  id: string;
  channel: SocialChannel;
  account_id: string;
  source_event_id: string;
  event_type: string;
  actor_handle: string;
  actor_name: string;
  text: string;
  pain_tags: string[];
  intent: string;
  urgency: "low" | "medium" | "high" | "critical";
  status: string;
  lead_id: string;
  duplicate_count: number;
  received_at: string;
}

export interface SocialDiagnosis {
  intent: string;
  pain_tags: string[];
  urgency: "low" | "medium" | "high" | "critical";
  maturity_stage: string;
  score: number;
  safe_reply: string;
}

export interface SocialOpsEventResult {
  created: boolean;
  event: SocialOpsEvent;
  diagnosis: SocialDiagnosis;
  lead: SocialLead;
}

export interface SocialPipelineColumn {
  id: string;
  label: string;
  leads: SocialLead[];
}

export interface SocialPipelineResponse {
  columns: SocialPipelineColumn[];
  summary: {
    total_leads: number;
    inbox_events: number;
    pending_approvals: number;
    high_risk_leads: number;
    connected_channels: number;
  };
}

export interface SocialChannelAccount {
  id: string;
  channel: SocialChannel;
  display_name: string;
  auth_status: string;
  notes: string;
  capability_status: Record<string, boolean>;
}

export interface SocialIntegrationsResponse {
  items: SocialChannelAccount[];
  policy: {
    whatsapp_enabled: boolean;
    sensitive_actions: string;
    booking: string;
  };
}

export interface SocialCommandDraft {
  id: string;
  status: string;
  action: string;
  risk_level: string;
  command_text: string;
  approval_reason: string;
}

export type IdeaStatus = "NUEVA" | "SELECCIONADA" | "USADA" | "DESCARTADA";

export interface Idea {
  id: number;
  tema_raw: string;
  pilar?: string | null;
  formato_sugerido?: string | null;
  status: IdeaStatus;
  score_potencial?: number | null;
}

export type CalendarioStatus = "PLANIFICADO" | "EN_PRODUCCION" | "DRAFT" | "REVIEW" | "APPROVED" | "PUBLISHED";

export interface Calendario {
  id: number;
  semana: number;
  fecha_publicacion: string;
  dia_semana: string;
  idea_id: number | null;
  pilar: string | null;
  formato: string | null;
  titulo_trabajo: string | null;
  status: CalendarioStatus;
  responsable: string;
  notas_editoriales: string | null;
  created_at: string;
}

export type ContenidoStatus = "BORRADOR_IA" | "EDITADO_HUMANO" | "APROBADO" | "LISTO_PUBLICAR";

export interface Contenido {
  id: number;
  cal_id: number;
  hook: string | null;
  hook_alt_1: string | null;
  hook_alt_2: string | null;
  copy_body: string | null;
  cta: string | null;
  hashtags: string | null;
  version: number;
  status: ContenidoStatus;
  qa_humanizacion: boolean;
  created_at: string;
}

export interface Metrica {
  id: number;
  pub_id: number;
  fecha_captura: string;
  alcance: number;
  impresiones: number;
  reacciones: number;
  comentarios: number;
  compartidos: number;
  engagement_rate: number;
  score?: number | null;
  clasificacion?: "GANADOR" | "PROMEDIO" | "PERDEDOR" | null;
}

export interface Publicacion {
  id: number;
  fecha_publicacion_real: string | null;
  plataforma: string;
}

export interface OnboardingStep {
  id: string;
  label: string;
  description: string;
}

export interface OnboardingWorkspace {
  id: string;
  company_name: string;
  customer_email: string;
  plan_name: string;
  owner_handle: string;
  sla?: { client_credentials_response_hours?: number };
  qa_targets?: { adoption_day7?: string };
}

export interface OnboardingSeedDraft {
  id: string;
  workspace_id: string;
  status: string;
  business_summary: string;
}

export interface OnboardingResponse {
  items: OnboardingWorkspace[];
  seed_drafts: OnboardingSeedDraft[];
  intake_items: Array<{
    id: string;
    workspace_id: string;
    source: string;
    actor_handle: string;
    text: string;
    extracted: Record<string, unknown>;
    present: string[];
    missing: string[];
    created_at: string;
  }>;
  template_steps: OnboardingStep[];
  policy: {
    trigger: string;
    sensitive_steps: string;
    connections: string[];
  };
}

const API_BASE = `${API_BASE_URL}/api/v1`;

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Social Ops API error ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getSocialOpsInbox() {
  return api<{ items: SocialOpsEvent[]; total: number; channels: SocialChannelAccount[] }>(
    "/social-ops/inbox"
  );
}

export function getSocialOpsPipeline() {
  return api<SocialPipelineResponse>("/social-ops/pipeline");
}

export function getSocialOpsIntegrations() {
  return api<SocialIntegrationsResponse>("/social-ops/integrations");
}

export function simulateSocialOpsEvent(payload: {
  channel: SocialChannel;
  event_type: string;
  text: string;
  actor_handle: string;
  actor_name?: string;
}) {
  return api<SocialOpsEventResult>("/social-ops/events/simulate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function diagnoseSocialOps(payload: { event_id?: string; lead_id?: string; notes?: string }) {
  return api<{ diagnosis: SocialDiagnosis; lead: SocialLead; handoff?: Record<string, unknown> | null }>(
    "/social-ops/diagnose",
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export function parseSocialOpsCommand(payload: {
  text: string;
  channel: SocialChannel;
  actor_handle?: string;
  lead_id?: string;
}) {
  return api<SocialCommandDraft>("/social-ops/commands/parse", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createSocialOpsLeadReplyDraft(payload: {
  lead_id: string;
  channel: SocialChannel;
  intent?: string;
  actor_handle?: string;
}) {
  return api<{
    id: string;
    type: string;
    lead_id: string;
    channel: SocialChannel;
    status: string;
    message_text: string;
  }>("/social-ops/leads/reply-draft", { method: "POST", body: JSON.stringify(payload) });
}

export function createSocialOpsSalesDraft(payload: {
  lead_id: string;
  channel: SocialChannel;
  actor_handle?: string;
}) {
  return api<{
    id: string;
    type: string;
    lead_id: string;
    channel: SocialChannel;
    status: string;
    message_text: string;
  }>("/social-ops/leads/sales-draft", { method: "POST", body: JSON.stringify(payload) });
}

export function getSocialOpsApprovals(limit = 200) {
  return api<{ items: any[]; total: number }>(`/social-ops/approvals?limit=${limit}`);
}

export function approveSocialOpsDraft(draftType: string, draftId: string, actorHandle: string) {
  return api<any>(`/social-ops/approvals/${draftType}/${draftId}/approve`, {
    method: "POST",
    body: JSON.stringify({ actor_handle: actorHandle }),
  });
}

export function rejectSocialOpsDraft(draftType: string, draftId: string, actorHandle: string, reason = "") {
  return api<any>(`/social-ops/approvals/${draftType}/${draftId}/reject`, {
    method: "POST",
    body: JSON.stringify({ actor_handle: actorHandle, reason }),
  });
}

export function getSocialOpsIdeas() {
  return api<{ source: "supabase" | "demo_fallback"; items: Idea[] }>("/social-ops/ideas");
}

export function updateSocialOpsIdeaStatus(id: number, status: IdeaStatus) {
  return api<{ ok: boolean }>(`/social-ops/ideas/${id}/status`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export function generateSocialOpsIdeaDraft(id: number) {
  return api<{ idea_id: number; draft_text: string }>(`/social-ops/ideas/${id}/generate-draft`, {
    method: "POST",
  });
}

export function getSocialOpsMetrics() {
  return api<{
    source: "supabase" | "demo_fallback";
    summary: { total_alcance: number; avg_engagement_rate: number; total_posts: number; best_score: number | null };
    metricas: Metrica[];
    publicaciones: Publicacion[];
  }>("/social-ops/metrics");
}

export function simulateSocialOpsMetrics() {
  return api<any>("/social-ops/metrics/simulate", { method: "POST" });
}

export function getSocialOpsCalendario(semana?: number) {
  const query = semana ? `?semana=${semana}` : "";
  return api<{ source: "supabase" | "demo_fallback"; items: Calendario[] }>(`/social-ops/calendario${query}`);
}

export function getSocialOpsBorradores() {
  return api<{ source: "supabase" | "demo_fallback"; items: Contenido[] }>("/social-ops/borradores");
}

export function approveSocialOpsBorrador(id: number, actorHandle = "ops_admin") {
  return api<{ ok: boolean }>(`/social-ops/borradores/${id}/approve`, {
    method: "POST",
    body: JSON.stringify({ actor_handle: actorHandle }),
  });
}

export function updateSocialOpsBorrador(id: number, updates: Partial<Contenido>) {
  return api<{ ok: boolean }>(`/social-ops/borradores/${id}/update`, {
    method: "POST",
    body: JSON.stringify(updates),
  });
}

export function getSocialOpsOnboarding() {
  return api<OnboardingResponse>("/social-ops/onboarding");
}

export function startSocialOpsOnboarding(payload: {
  company_name: string;
  customer_email: string;
  payment_reference: string;
  plan_name: string;
  owner_handle?: string;
  requested_channels?: string[];
}) {
  return api<OnboardingWorkspace>("/social-ops/onboarding/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function advanceSocialOpsOnboardingStep(
  workspaceId: string,
  stepId: string,
  payload: { status: string; notes?: string }
) {
  return api<OnboardingWorkspace>(`/social-ops/onboarding/${workspaceId}/steps/${stepId}/advance`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createSocialOpsOnboardingSeed(
  workspaceId: string,
  payload: { business_summary?: string; initial_channels?: string[] }
) {
  return api<OnboardingSeedDraft>(`/social-ops/onboarding/${workspaceId}/seed`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function intakeSocialOpsOnboarding(
  workspaceId: string,
  payload: { text: string; source?: string; actor_handle?: string }
) {
  return api<{
    id: string;
    workspace_id: string;
    source: string;
    actor_handle: string;
    text: string;
    extracted: Record<string, unknown>;
    present: string[];
    missing: string[];
    created_at: string;
  }>(`/social-ops/onboarding/${workspaceId}/intake`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
