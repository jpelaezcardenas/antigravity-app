import React, { useEffect, useState } from 'react';
import {
  createSocialOpsOnboardingSeed,
  getSocialOpsOnboarding,
  intakeSocialOpsOnboarding,
  startSocialOpsOnboarding,
  type OnboardingResponse,
  type OnboardingWorkspace,
} from '../../lib/socialOpsApi';

function Badge({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold ${className}`}>
      {children}
    </span>
  );
}

export default function OnboardingOps() {
  const [onboarding, setOnboarding] = useState<OnboardingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState('');
  const [lastIntake, setLastIntake] = useState<any>(null);
  const [onboardingStartForm, setOnboardingStartForm] = useState({
    company_name: 'Cliente Nuevo SAS',
    customer_email: 'cliente@demo.co',
    payment_reference: 'pay_demo_001',
    plan_name: 'Starter',
    owner_handle: '@cliente',
    requested_channels: ['telegram', 'instagram', 'linkedin'],
  });
  const [intakeText, setIntakeText] = useState(
    'Nuestro NIT es 901234567-8. Usamos Siigo. Bancolombia y Nequi. Tenemos Stripe. No tengo RUT aun.'
  );

  const refresh = async () => {
    setError('');
    try {
      const onboardingResponse = await getSocialOpsOnboarding();
      setOnboarding(onboardingResponse);
      if (!selectedWorkspaceId && onboardingResponse.items.length > 0) {
        setSelectedWorkspaceId(onboardingResponse.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar Onboarding 21D');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleStartOnboarding = async (event: React.FormEvent) => {
    event.preventDefault();
    setActionMessage('');
    setError('');
    try {
      const workspace = await startSocialOpsOnboarding(onboardingStartForm);
      setSelectedWorkspaceId(workspace.id);
      setActionMessage('Onboarding iniciado (S1 kick-off en pending_approval)');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar el onboarding');
    }
  };

  const handleIntake = async (event: React.FormEvent) => {
    event.preventDefault();
    setActionMessage('');
    setError('');
    if (!selectedWorkspaceId) {
      setError('Selecciona un workspace de onboarding');
      return;
    }
    try {
      const intake = await intakeSocialOpsOnboarding(selectedWorkspaceId, {
        text: intakeText,
        source: 'dashboard',
        actor_handle: onboardingStartForm.owner_handle,
      });
      setLastIntake(intake);
      setActionMessage('Intake recibido: credenciales presentes/faltantes detectadas');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo procesar el intake');
    }
  };

  const handleCreateSeed = async () => {
    setActionMessage('');
    setError('');
    if (!selectedWorkspaceId) {
      setError('Selecciona un workspace de onboarding');
      return;
    }
    try {
      await createSocialOpsOnboardingSeed(selectedWorkspaceId, {
        business_summary: 'Onboarding 21D: CFO + Escudo Legal, plomeria de datos + Auditoria Sombra.',
        initial_channels: onboardingStartForm.requested_channels,
      });
      setActionMessage('Seed draft creado en pending_approval');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el seed draft');
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[360px] place-items-center rounded-lg border border-slate-700 bg-slate-950/60">
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Cargando Onboarding 21D</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300">Onboarding 21D</p>
            <h3 className="text-lg font-semibold text-white">De firma a Pulso Diario en 21 dias</h3>
            <p className="text-xs text-slate-500">S1/S2/S3 + Go-Live, sin duplicarse dentro de Operaciones.</p>
          </div>
          <Badge className="border-cyan-500/30 bg-cyan-500/10 text-cyan-200">Sidebar Onboarding</Badge>
        </div>
      </section>

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

      <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
        <form onSubmit={handleStartOnboarding} className="space-y-4 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Onboarding 21D</h3>
            <p className="text-xs text-slate-500">De firma a Pulso Diario en 21 dias (S1/S2/S3 + Go-Live).</p>
          </div>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Empresa</span>
            <input
              value={onboardingStartForm.company_name}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, company_name: event.target.value }))}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Email</span>
            <input
              value={onboardingStartForm.customer_email}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, customer_email: event.target.value }))}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pago / referencia</span>
            <input
              value={onboardingStartForm.payment_reference}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, payment_reference: event.target.value }))}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Plan</span>
            <input
              value={onboardingStartForm.plan_name}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, plan_name: event.target.value }))}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Owner handle</span>
            <input
              value={onboardingStartForm.owner_handle}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, owner_handle: event.target.value }))}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </label>
          <button className="w-full rounded-md bg-emerald-400 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-300">
            Iniciar onboarding
          </button>
        </form>

        <div className="space-y-4">
          <section className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">Workspace</h3>
                <p className="text-xs text-slate-500">Selecciona un cliente para intake y seed.</p>
              </div>
              <select
                value={selectedWorkspaceId}
                onChange={(event) => setSelectedWorkspaceId(event.target.value)}
                className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
              >
                <option value="">Sin workspace</option>
                {(onboarding?.items || []).map((ws: OnboardingWorkspace) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.company_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {(onboarding?.items || [])
                .filter((ws: OnboardingWorkspace) => ws.id === selectedWorkspaceId)
                .map((ws: OnboardingWorkspace) => (
                  <React.Fragment key={ws.id}>
                    <div className="rounded-md border border-slate-700 bg-slate-900/60 p-3">
                      <p className="text-xs uppercase tracking-wider text-slate-400">SLA credenciales</p>
                      <p className="mt-1 text-sm text-slate-200">{ws.sla?.client_credentials_response_hours ?? 48}h</p>
                    </div>
                    <div className="rounded-md border border-slate-700 bg-slate-900/60 p-3">
                      <p className="text-xs uppercase tracking-wider text-slate-400">QA adopcion dia 7</p>
                      <p className="mt-1 text-sm text-slate-200">{ws.qa_targets?.adoption_day7 ?? '>=3 logins/7d'}</p>
                    </div>
                  </React.Fragment>
                ))}
            </div>
          </section>

          <form onSubmit={handleIntake} className="space-y-3 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Intake sin formularios</h3>
              <p className="text-xs text-slate-500">
                Pega hechos en lenguaje natural; la IA extrae credenciales presentes/faltantes y datos base.
              </p>
            </div>
            <textarea
              value={intakeText}
              onChange={(event) => setIntakeText(event.target.value)}
              rows={5}
              className="w-full resize-none rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
            <div className="flex flex-col gap-2 md:flex-row">
              <button className="flex-1 rounded-md bg-cyan-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-cyan-300">
                Analizar intake
              </button>
              <button
                type="button"
                onClick={handleCreateSeed}
                className="flex-1 rounded-md bg-amber-400 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-amber-300"
              >
                Crear seed draft
              </button>
            </div>
            {lastIntake && (
              <div className="rounded-md border border-slate-700 bg-slate-900/60 p-3 text-sm text-slate-200">
                <div className="flex flex-wrap gap-2">
                  <Badge className="border-emerald-500/40 bg-emerald-500/10 text-emerald-200">
                    presentes: {lastIntake.present.length}
                  </Badge>
                  <Badge className="border-rose-500/40 bg-rose-500/10 text-rose-200">
                    faltantes: {lastIntake.missing.length}
                  </Badge>
                </div>
                <p className="mt-3 text-xs text-slate-400">Faltantes: {(lastIntake.missing || []).join(', ') || 'ninguno'}</p>
              </div>
            )}
          </form>

          <section className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <h3 className="text-lg font-semibold text-white">Checklist (pasos)</h3>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {(onboarding?.template_steps || []).map((step) => (
                <div key={step.id} className="rounded-md border border-slate-700 bg-slate-900/60 p-3">
                  <p className="text-sm font-semibold text-white">{step.label}</p>
                  <p className="mt-1 text-xs text-slate-400">{step.description}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
