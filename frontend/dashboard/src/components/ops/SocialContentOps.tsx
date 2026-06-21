import React, { useEffect, useMemo, useState } from 'react';
import BorradoresReview from './BorradoresReview';
import CalendarioEditorial from './CalendarioEditorial';
import MetricasDashboard from './MetricasDashboard';
import IdeasOps from './IdeasOps';
import {
  diagnoseSocialOps,
  getSocialOpsInbox,
  getSocialOpsIntegrations,
  getSocialOpsPipeline,
  createSocialOpsLeadReplyDraft,
  createSocialOpsSalesDraft,
  getSocialOpsApprovals,
  approveSocialOpsDraft,
  rejectSocialOpsDraft,
  parseSocialOpsCommand,
  simulateSocialOpsEvent,
  type SocialChannel,
  type SocialCommandDraft,
  type SocialDiagnosis,
  type SocialIntegrationsResponse,
  type SocialOpsEvent,
  type SocialPipelineResponse,
} from '../../lib/socialOpsApi';

type OpsTab = 'inbox' | 'pipeline' | 'commands' | 'approvals' | 'integrations';

const CHANNELS: Array<{ value: SocialChannel; label: string; short: string }> = [
  { value: 'telegram', label: 'Telegram', short: 'TG' },
  { value: 'facebook', label: 'Facebook', short: 'FB' },
  { value: 'instagram', label: 'Instagram', short: 'IG' },
  { value: 'tiktok', label: 'TikTok', short: 'TT' },
  { value: 'linkedin', label: 'LinkedIn', short: 'LI' },
];

const TABS: Array<{ id: OpsTab; label: string }> = [
  { id: 'inbox', label: 'Inbox' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'commands', label: 'Comandos' },
  { id: 'approvals', label: 'Aprobaciones' },
  { id: 'integrations', label: 'Integraciones' },
];

type OpsLegacyTab = 'ideas' | 'calendario' | 'borradores' | 'metricas';
const LEGACY_TABS: Array<{ id: OpsLegacyTab; label: string }> = [
  { id: 'ideas', label: 'Ideas' },
  { id: 'calendario', label: 'Calendario' },
  { id: 'borradores', label: 'Borradores' },
  { id: 'metricas', label: 'Métricas' },
];

const urgencyStyles: Record<string, string> = {
  low: 'border-slate-600/60 bg-slate-800/50 text-ink',
  medium: 'border-amber-500/40 bg-amber-500/10 text-amber-200',
  high: 'border-orange-500/40 bg-orange-500/10 text-orange-200',
  critical: 'border-rose-500/50 bg-rose-500/10 text-rose-200',
};

const stageAccent: Record<string, string> = {
  nuevo: 'border-slate-500/30',
  diagnosticado: 'border-primary/40',
  auditoria_sombra: 'border-amber-500/40',
  formalizacion: 'border-emerald-500/40',
  activacion_fase2: 'border-violet-500/40',
  escalado_entidad_a: 'border-rose-500/50',
  cerrado: 'border-slate-600/50',
};

function channelShort(channel: SocialChannel) {
  return CHANNELS.find((item) => item.value === channel)?.short || channel.slice(0, 2).toUpperCase();
}

function painLabel(tag: string) {
  return tag.replace(/_/g, ' ');
}

function Stat({ label, value, tone }: { label: string; value: number | string; tone: string }) {
  return (
    <div className={`rounded-lg border ${tone} p-4`}>
      <p className="text-[11px] uppercase tracking-wider text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function Badge({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold ${className}`}>
      {children}
    </span>
  );
}

const SocialContentOps: React.FC = () => {
  const [activeTab, setActiveTab] = useState<OpsTab>('inbox');
  const [activeLegacy, setActiveLegacy] = useState<OpsLegacyTab>('ideas');
  const [inbox, setInbox] = useState<SocialOpsEvent[]>([]);
  const [pipeline, setPipeline] = useState<SocialPipelineResponse | null>(null);
  const [integrations, setIntegrations] = useState<SocialIntegrationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState('');
  const [error, setError] = useState('');
  const [lastDiagnosis, setLastDiagnosis] = useState<SocialDiagnosis | null>(null);
  const [lastDraft, setLastDraft] = useState<SocialCommandDraft | null>(null);
  const [lastOutboundDraft, setLastOutboundDraft] = useState<any>(null);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [approvalActor, setApprovalActor] = useState('ops_admin');
  const [rejectionReason, setRejectionReason] = useState('No aprobado por politica / requiere revision humana');
  const [simulateForm, setSimulateForm] = useState({
    channel: 'instagram' as SocialChannel,
    actor_handle: '@prospecto_amva',
    text: 'Tengo multa DIAN por vender en TikTok y no se si necesito RUT.',
  });
  const [commandForm, setCommandForm] = useState({
    channel: 'telegram' as SocialChannel,
    actor_handle: 'ctx_operator',
    text: '/ops conectar Stripe y crear centro de costos TikTok',
  });

  const refresh = async () => {
    setError('');
    try {
      const [inboxResponse, pipelineResponse, integrationsResponse, approvalsResponse] = await Promise.all([
        getSocialOpsInbox(),
        getSocialOpsPipeline(),
        getSocialOpsIntegrations(),
        getSocialOpsApprovals(200),
      ]);
      setInbox(inboxResponse.items);
      setPipeline(pipelineResponse);
      setIntegrations(integrationsResponse);
      setApprovals(approvalsResponse.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar Social Content Ops');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const summary = pipeline?.summary || {
    total_leads: 0,
    inbox_events: 0,
    pending_approvals: 0,
    high_risk_leads: 0,
    connected_channels: 0,
  };

  const activeLeads = useMemo(
    () => pipeline?.columns.flatMap((column) => column.leads).filter((lead) => lead.pipeline_stage !== 'cerrado') || [],
    [pipeline]
  );

  const handleSimulate = async (event: React.FormEvent) => {
    event.preventDefault();
    setActionMessage('');
    setError('');
    try {
      const result = await simulateSocialOpsEvent({
        channel: simulateForm.channel,
        event_type: simulateForm.channel === 'telegram' ? 'message' : 'comment',
        text: simulateForm.text,
        actor_handle: simulateForm.actor_handle,
      });
      setLastDiagnosis(result.diagnosis);
      setActionMessage(result.created ? 'Evento inbound registrado' : 'Evento duplicado detectado');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo simular el evento');
    }
  };

  const handleDiagnose = async (eventId: string) => {
    setActionMessage('');
    setError('');
    try {
      const result = await diagnoseSocialOps({ event_id: eventId });
      setLastDiagnosis(result.diagnosis);
      setActionMessage(result.handoff ? 'Handoff preparado para Entidad A' : 'Diagnostico actualizado');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo diagnosticar el evento');
    }
  };

  const handleCommand = async (event: React.FormEvent) => {
    event.preventDefault();
    setActionMessage('');
    setError('');
    try {
      const draft = await parseSocialOpsCommand(commandForm);
      setLastDraft(draft);
      setActionMessage('Borrador creado en pending_approval');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo interpretar el comando');
    }
  };

  const handleDraftReply = async (leadId: string, channel: SocialChannel) => {
    setActionMessage('');
    setError('');
    try {
      const draft = await createSocialOpsLeadReplyDraft({ lead_id: leadId, channel, actor_handle: 'taty' });
      setLastOutboundDraft(draft);
      setActionMessage('Borrador de respuesta creado (pending_approval)');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el borrador de respuesta');
    }
  };

  const handleDraftSales = async (leadId: string, channel: SocialChannel) => {
    setActionMessage('');
    setError('');
    try {
      const draft = await createSocialOpsSalesDraft({ lead_id: leadId, channel, actor_handle: 'taty' });
      setLastOutboundDraft(draft);
      setActionMessage('Borrador de cierre creado (pending_approval)');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el borrador de cierre');
    }
  };

  const handleApprove = async (item: any) => {
    setActionMessage('');
    setError('');
    try {
      await approveSocialOpsDraft(item.type, item.id, approvalActor);
      setActionMessage('Aprobado');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo aprobar');
    }
  };

  const handleReject = async (item: any) => {
    setActionMessage('');
    setError('');
    try {
      await rejectSocialOpsDraft(item.type, item.id, approvalActor, rejectionReason);
      setActionMessage('Rechazado');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo rechazar');
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[360px] place-items-center rounded-lg border border-slate-700 bg-slate-950/60">
        <p className="text-sm uppercase tracking-[0.2em] text-primary">Cargando Social Content Ops</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-outline/40 bg-gradient-to-r from-slate-950 via-slate-950 to-cyan-950/30 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-primary">Bunker operativo</p>
            <h2 className="mt-1 text-2xl font-bold text-white">Social Media OPs Systems</h2>
            <p className="mt-1 max-w-3xl text-sm text-primary/70">
              Motor de contenido orgánico para Facebook, Instagram, TikTok, LinkedIn y Telegram — Contexia.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {CHANNELS.map((channel) => (
              <Badge key={channel.value} className="border-primary/30 bg-primary/10 text-primary">
                {channel.short} {channel.label}
              </Badge>
            ))}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-5">
          <Stat label="Leads activos" value={activeLeads.length} tone="border-primary/30 bg-primary/10" />
          <Stat label="Eventos inbox" value={summary.inbox_events} tone="border-slate-600/50 bg-slate-800/50" />
          <Stat label="Riesgo alto" value={summary.high_risk_leads} tone="border-rose-500/40 bg-rose-500/10" />
          <Stat label="Aprobaciones" value={summary.pending_approvals} tone="border-amber-500/40 bg-amber-500/10" />
          <Stat label="Canales activos" value={summary.connected_channels} tone="border-emerald-500/40 bg-emerald-500/10" />
        </div>
      </section>

      <div className="rounded-2xl border border-outline/40 bg-white/5 p-2">
        <div className="grid grid-cols-4 gap-2">
          {LEGACY_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveLegacy(tab.id)}
              className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${
                activeLegacy === tab.id ? 'bg-primary/15 text-primary border border-primary/20' : 'text-muted hover:bg-white/5 border border-transparent'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-1 overflow-x-auto rounded-2xl border border-outline/40 bg-white/5 p-1.5">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`min-w-28 flex-1 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === tab.id
                ? 'bg-primary/15 text-primary ring-1 ring-primary/30'
                : 'text-muted hover:bg-white/5 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {(error || actionMessage) && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            error
              ? 'border-rose-500/40 bg-rose-500/10 text-rose-200'
              : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
          }`}
        >
          {error || actionMessage}
        </div>
      )}

      {activeLegacy === 'ideas' && <IdeasOps />}
      {activeLegacy === 'calendario' && <CalendarioEditorial />}
      {activeLegacy === 'borradores' && <BorradoresReview />}
      {activeLegacy === 'metricas' && <MetricasDashboard />}

      {activeTab === 'inbox' && (
        <div className="grid gap-5 xl:grid-cols-[380px_minmax(0,1fr)]">
          <form onSubmit={handleSimulate} className="space-y-4 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Simulador inbound</h3>
              <p className="text-xs text-muted">Smoke test local de eventos normalizados.</p>
            </div>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Canal</span>
              <select
                value={simulateForm.channel}
                onChange={(event) => setSimulateForm((prev) => ({ ...prev, channel: event.target.value as SocialChannel }))}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              >
                {CHANNELS.map((channel) => (
                  <option key={channel.value} value={channel.value}>
                    {channel.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Handle</span>
              <input
                value={simulateForm.actor_handle}
                onChange={(event) => setSimulateForm((prev) => ({ ...prev, actor_handle: event.target.value }))}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Mensaje</span>
              <textarea
                value={simulateForm.text}
                onChange={(event) => setSimulateForm((prev) => ({ ...prev, text: event.target.value }))}
                rows={5}
                className="mt-1 w-full resize-none rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              />
            </label>
            <button className="w-full rounded-md bg-primary px-4 py-2 text-sm font-bold text-obsidian hover:bg-primary-dim">
              Crear evento
            </button>
            {lastDiagnosis && (
              <div className="rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">
                <p className="font-semibold">{lastDiagnosis.maturity_stage}</p>
                <p className="mt-1 text-xs text-primary/80">{lastDiagnosis.safe_reply}</p>
              </div>
            )}
          </form>

          <div className="space-y-3">
            {inbox.length === 0 ? (
              <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-8 text-center text-muted">
                Inbox sin eventos.
              </div>
            ) : (
              inbox.map((event) => (
                <article key={event.id} className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge className="border-primary/30 bg-primary/10 text-primary">
                          {channelShort(event.channel)}
                        </Badge>
                        <Badge className={urgencyStyles[event.urgency] || urgencyStyles.low}>
                          {event.urgency}
                        </Badge>
                        <span className="text-xs text-muted">{event.event_type}</span>
                      </div>
                      <h4 className="mt-2 text-sm font-semibold text-white">{event.actor_name || event.actor_handle}</h4>
                      <p className="mt-1 text-sm leading-6 text-muted">{event.text}</p>
                    </div>
                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => handleDiagnose(event.id)}
                        className="rounded-md border border-primary/40 px-3 py-2 text-xs font-semibold text-primary hover:bg-primary/10"
                      >
                        Diagnosticar
                      </button>
                      <button
                        onClick={() => handleDraftSales(event.lead_id, event.channel)}
                        className="rounded-md border border-amber-500/40 px-3 py-2 text-xs font-semibold text-amber-200 hover:bg-amber-500/10"
                      >
                        Draft cierre
                      </button>
                    </div>
                  </div>
                  {event.pain_tags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {event.pain_tags.map((tag) => (
                        <Badge key={tag} className="border-slate-600 bg-slate-800 text-muted">
                          {painLabel(tag)}
                        </Badge>
                      ))}
                    </div>
                  )}
                </article>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'pipeline' && (
        <div className="grid gap-4 xl:grid-cols-4">
          {pipeline?.columns.map((column) => (
            <section key={column.id} className={`rounded-lg border ${stageAccent[column.id] || 'border-slate-700'} bg-slate-950/60 p-3`}>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">{column.label}</h3>
                <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-muted">{column.leads.length}</span>
              </div>
              <div className="mt-3 space-y-3">
                {column.leads.length === 0 ? (
                  <p className="rounded-md border border-dashed border-slate-700 p-3 text-xs text-muted">Sin leads.</p>
                ) : (
                  column.leads.map((lead) => (
                    <article key={lead.id} className="rounded-md border border-slate-700 bg-slate-900/70 p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold text-white">{lead.display_name}</p>
                          <p className="text-xs text-muted">{lead.actor_handle}</p>
                        </div>
                        <Badge className={urgencyStyles[lead.urgency] || urgencyStyles.low}>{lead.urgency}</Badge>
                      </div>
                      <p className="mt-2 text-xs text-primary">{lead.maturity_stage}</p>
                      <p className="mt-2 text-xs leading-5 text-muted">{lead.last_message}</p>
                      <div className="mt-3 grid grid-cols-2 gap-2">
                        <button
                          onClick={() => handleDraftReply(lead.id, lead.primary_channel)}
                          className="rounded-md border border-primary/40 px-2 py-1.5 text-xs font-semibold text-primary hover:bg-primary/10"
                        >
                          Draft reply
                        </button>
                        <button
                          onClick={() => handleDraftSales(lead.id, lead.primary_channel)}
                          className="rounded-md border border-amber-500/40 px-2 py-1.5 text-xs font-semibold text-amber-200 hover:bg-amber-500/10"
                        >
                          Draft cierre
                        </button>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {lead.pain_tags.map((tag) => (
                          <Badge key={tag} className="border-slate-600 bg-slate-800 text-muted">
                            {painLabel(tag)}
                          </Badge>
                        ))}
                      </div>
                    </article>
                  ))
                )}
              </div>
            </section>
          ))}
        </div>
      )}

      {lastOutboundDraft && (
        <section className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-lg font-semibold text-white">Ultimo borrador outbound</h3>
            <Badge className="border-amber-500/40 bg-amber-500/10 text-amber-200">{lastOutboundDraft.status}</Badge>
          </div>
          <p className="mt-3 rounded-md border border-slate-700 bg-slate-900 p-3 text-sm leading-6 text-ink">
            {lastOutboundDraft.message_text}
          </p>
          <p className="mt-2 text-xs text-muted">{lastOutboundDraft.approval_reason}</p>
        </section>
      )}

      {activeTab === 'commands' && (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,460px)_minmax(0,1fr)]">
          <form onSubmit={handleCommand} className="space-y-4 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Zero-UI por Telegram</h3>
              <p className="text-xs text-muted">Los comandos quedan como borradores aprobables.</p>
            </div>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Canal</span>
              <select
                value={commandForm.channel}
                onChange={(event) => setCommandForm((prev) => ({ ...prev, channel: event.target.value as SocialChannel }))}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              >
                {CHANNELS.map((channel) => (
                  <option key={channel.value} value={channel.value}>
                    {channel.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Operador</span>
              <input
                value={commandForm.actor_handle}
                onChange={(event) => setCommandForm((prev) => ({ ...prev, actor_handle: event.target.value }))}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Comando</span>
              <textarea
                value={commandForm.text}
                onChange={(event) => setCommandForm((prev) => ({ ...prev, text: event.target.value }))}
                rows={5}
                className="mt-1 w-full resize-none rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              />
            </label>
            <button className="w-full rounded-md bg-amber-400 px-4 py-2 text-sm font-bold text-obsidian hover:bg-amber-300">
              Crear borrador
            </button>
          </form>

          <section className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <h3 className="text-lg font-semibold text-white">Borrador activo</h3>
            {lastDraft ? (
              <div className="mt-4 space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Badge className="border-amber-500/40 bg-amber-500/10 text-amber-200">{lastDraft.status}</Badge>
                  <Badge className="border-primary/30 bg-primary/10 text-primary">{lastDraft.action}</Badge>
                  <Badge className="border-slate-600 bg-slate-800 text-muted">{lastDraft.risk_level}</Badge>
                </div>
                <p className="rounded-md border border-slate-700 bg-slate-900 p-3 text-sm leading-6 text-muted">
                  {lastDraft.command_text}
                </p>
                <p className="text-sm text-muted">{lastDraft.approval_reason}</p>
              </div>
            ) : (
              <p className="mt-4 text-sm text-muted">Sin borrador seleccionado.</p>
            )}
          </section>
        </div>
      )}

      {activeTab === 'approvals' && (
        <section className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-lg font-semibold text-white">Human-in-the-Loop</h3>
              <p className="text-xs text-muted">
                Todo outbound y toda accion sensible queda en pending_approval hasta que un humano apruebe o rechace.
              </p>
            </div>
            <Badge className="border-amber-500/40 bg-amber-500/10 text-amber-200">{approvals.length} pendientes</Badge>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Aprobador</span>
              <input
                value={approvalActor}
                onChange={(event) => setApprovalActor(event.target.value)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Motivo rechazo</span>
              <input
                value={rejectionReason}
                onChange={(event) => setRejectionReason(event.target.value)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-primary"
              />
            </label>
          </div>
          <div className="mt-4 space-y-3">
            {approvals.length === 0 ? (
              <p className="rounded-md border border-dashed border-slate-700 p-6 text-center text-sm text-muted">
                Sin aprobaciones pendientes.
              </p>
            ) : (
              approvals.map((item) => (
                <div key={`${item.type}:${item.id}`} className="rounded-md border border-slate-700 bg-slate-900/60 p-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge className="border-primary/30 bg-primary/10 text-primary">{item.type}</Badge>
                        <Badge className="border-amber-500/40 bg-amber-500/10 text-amber-200">{item.status}</Badge>
                        <span className="text-xs text-muted">{item.created_at}</span>
                      </div>
                      <p className="mt-2 text-sm text-ink">{item.summary}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(item)}
                        className="rounded-md bg-emerald-400 px-3 py-2 text-xs font-bold text-obsidian hover:bg-emerald-300"
                      >
                        Aprobar
                      </button>
                      <button
                        onClick={() => handleReject(item)}
                        className="rounded-md border border-rose-500/40 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-500/10"
                      >
                        Rechazar
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      )}

      {activeTab === 'integrations' && (
        <div className="grid gap-4 lg:grid-cols-2">
          {integrations?.items.map((account) => (
            <article key={account.id} className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge className="border-primary/30 bg-primary/10 text-primary">
                      {channelShort(account.channel)}
                    </Badge>
                    <h3 className="text-base font-semibold text-white">{account.display_name}</h3>
                  </div>
                  <p className="mt-2 text-sm text-muted">{account.notes}</p>
                </div>
                <Badge className="border-slate-600 bg-slate-800 text-muted">{account.auth_status}</Badge>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {Object.entries(account.capability_status).map(([capability, enabled]) => (
                  <Badge
                    key={capability}
                    className={
                      enabled
                        ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                        : 'border-slate-600 bg-slate-800 text-muted'
                    }
                  >
                    {capability.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </article>
          ))}
          {integrations && (
            <section className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 lg:col-span-2">
              <h3 className="text-base font-semibold text-amber-100">Politica de seguridad</h3>
              <div className="mt-3 grid gap-3 text-sm text-amber-100 md:grid-cols-3">
                <p>WhatsApp: {integrations.policy.whatsapp_enabled ? 'habilitado' : 'fuera del despliegue'}</p>
                <p>Acciones sensibles: {integrations.policy.sensitive_actions}</p>
                <p>Agendamiento: {integrations.policy.booking}</p>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
};

export default SocialContentOps;
