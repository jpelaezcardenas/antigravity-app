"use client";

import { useEffect, useState } from "react";
import {
  createSocialOpsOnboardingSeed,
  getSocialOpsOnboarding,
  intakeSocialOpsOnboarding,
  startSocialOpsOnboarding,
  type OnboardingResponse,
  type OnboardingWorkspace,
} from "@/lib/social-ops-api";

function Badge({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold ${className}`}>
      {children}
    </span>
  );
}

export function OnboardingSection() {
  const [onboarding, setOnboarding] = useState<OnboardingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [lastIntake, setLastIntake] = useState<any>(null);
  const [onboardingStartForm, setOnboardingStartForm] = useState({
    company_name: "Cliente Nuevo SAS",
    customer_email: "cliente@demo.co",
    payment_reference: "pay_demo_001",
    plan_name: "Starter",
    owner_handle: "@cliente",
  });
  const [intakeText, setIntakeText] = useState(
    "Nuestro NIT es 901234567-8. Usamos Siigo. Bancolombia y Nequi. Tenemos Stripe. No tengo RUT aun."
  );

  const refresh = async () => {
    setError("");
    try {
      const onboardingResponse = await getSocialOpsOnboarding();
      setOnboarding(onboardingResponse);
      if (!selectedWorkspaceId && onboardingResponse.items.length > 0) {
        setSelectedWorkspaceId(onboardingResponse.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar Onboarding 21D");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleStartOnboarding = async (event: React.FormEvent) => {
    event.preventDefault();
    setActionMessage("");
    setError("");
    try {
      const workspace = await startSocialOpsOnboarding({
        ...onboardingStartForm,
        requested_channels: ["telegram", "instagram", "linkedin"],
      });
      setSelectedWorkspaceId(workspace.id);
      setActionMessage("Onboarding iniciado (S1 kick-off en pending_approval)");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar el onboarding");
    }
  };

  const handleIntake = async (event: React.FormEvent) => {
    event.preventDefault();
    setActionMessage("");
    setError("");
    if (!selectedWorkspaceId) {
      setError("Selecciona un workspace de onboarding");
      return;
    }
    try {
      const intake = await intakeSocialOpsOnboarding(selectedWorkspaceId, {
        text: intakeText,
        source: "dashboard",
        actor_handle: onboardingStartForm.owner_handle,
      });
      setLastIntake(intake);
      setActionMessage("Intake recibido: credenciales presentes/faltantes detectadas");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo procesar el intake");
    }
  };

  const handleCreateSeed = async () => {
    setActionMessage("");
    setError("");
    if (!selectedWorkspaceId) {
      setError("Selecciona un workspace de onboarding");
      return;
    }
    try {
      await createSocialOpsOnboardingSeed(selectedWorkspaceId, {
        business_summary: "Onboarding 21D: CFO + Escudo Legal, plomeria de datos + Auditoria Sombra.",
        initial_channels: ["telegram", "instagram", "linkedin"],
      });
      setActionMessage("Seed draft creado en pending_approval");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el seed draft");
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[360px] place-items-center rounded-lg border border-outline-variant/20 bg-surface-container">
        <p className="text-sm uppercase tracking-[0.2em] text-primary-container">Cargando Onboarding 21D</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-outline-variant/20 bg-surface-container p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-primary-container">Onboarding 21D</p>
            <h3 className="text-lg font-semibold text-on-surface">De firma a Pulso Diario en 21 dias</h3>
            <p className="text-xs text-on-surface-variant">S1/S2/S3 + Go-Live, sin duplicarse dentro de Operaciones.</p>
          </div>
          <Badge className="border-primary/30 bg-primary/10 text-primary-container">Sidebar Onboarding</Badge>
        </div>
      </section>

      {(error || actionMessage) && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            error
              ? "border-status-critical/40 bg-status-critical/10 text-status-critical"
              : "border-status-success/40 bg-status-success/10 text-status-success"
          }`}
        >
          {error || actionMessage}
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
        <form onSubmit={handleStartOnboarding} className="space-y-4 rounded-lg border border-outline-variant/20 bg-surface-container p-4">
          <div>
            <h3 className="text-lg font-semibold text-on-surface">Onboarding 21D</h3>
            <p className="text-xs text-on-surface-variant">De firma a Pulso Diario en 21 dias (S1/S2/S3 + Go-Live).</p>
          </div>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Empresa</span>
            <input
              value={onboardingStartForm.company_name}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, company_name: event.target.value }))}
              className="mt-1 w-full rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Email</span>
            <input
              value={onboardingStartForm.customer_email}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, customer_email: event.target.value }))}
              className="mt-1 w-full rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Pago / referencia</span>
            <input
              value={onboardingStartForm.payment_reference}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, payment_reference: event.target.value }))}
              className="mt-1 w-full rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Plan</span>
            <input
              value={onboardingStartForm.plan_name}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, plan_name: event.target.value }))}
              className="mt-1 w-full rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Owner handle</span>
            <input
              value={onboardingStartForm.owner_handle}
              onChange={(event) => setOnboardingStartForm((prev) => ({ ...prev, owner_handle: event.target.value }))}
              className="mt-1 w-full rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
            />
          </label>
          <button className="w-full rounded-md bg-status-success px-4 py-2 text-sm font-bold text-on-primary hover:bg-status-success/90">
            Iniciar onboarding
          </button>
        </form>

        <div className="space-y-4">
          <section className="rounded-lg border border-outline-variant/20 bg-surface-container p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-on-surface">Workspace</h3>
                <p className="text-xs text-on-surface-variant">Selecciona un cliente para intake y seed.</p>
              </div>
              <select
                value={selectedWorkspaceId}
                onChange={(event) => setSelectedWorkspaceId(event.target.value)}
                className="rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
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
                  <div key={ws.id} className="contents">
                    <div className="rounded-md border border-outline-variant/20 bg-surface-elevated p-3">
                      <p className="text-xs uppercase tracking-wider text-on-surface-variant">SLA credenciales</p>
                      <p className="mt-1 text-sm text-on-surface">{ws.sla?.client_credentials_response_hours ?? 48}h</p>
                    </div>
                    <div className="rounded-md border border-outline-variant/20 bg-surface-elevated p-3">
                      <p className="text-xs uppercase tracking-wider text-on-surface-variant">QA adopcion dia 7</p>
                      <p className="mt-1 text-sm text-on-surface">{ws.qa_targets?.adoption_day7 ?? ">=3 logins/7d"}</p>
                    </div>
                  </div>
                ))}
            </div>
          </section>

          <form onSubmit={handleIntake} className="space-y-3 rounded-lg border border-outline-variant/20 bg-surface-container p-4">
            <div>
              <h3 className="text-lg font-semibold text-on-surface">Intake sin formularios</h3>
              <p className="text-xs text-on-surface-variant">
                Pega hechos en lenguaje natural; la IA extrae credenciales presentes/faltantes y datos base.
              </p>
            </div>
            <textarea
              value={intakeText}
              onChange={(event) => setIntakeText(event.target.value)}
              rows={5}
              className="w-full resize-none rounded-md border border-outline-variant/30 bg-surface-elevated px-3 py-2 text-sm text-on-surface outline-none focus:border-primary"
            />
            <div className="flex flex-col gap-2 md:flex-row">
              <button className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-bold text-on-primary hover:bg-primary-fixed-dim">
                Analizar intake
              </button>
              <button
                type="button"
                onClick={handleCreateSeed}
                className="flex-1 rounded-md bg-status-warning px-4 py-2 text-sm font-bold text-on-primary hover:bg-status-warning/90"
              >
                Crear seed draft
              </button>
            </div>
            {lastIntake && (
              <div className="rounded-md border border-outline-variant/20 bg-surface-elevated p-3 text-sm text-on-surface">
                <div className="flex flex-wrap gap-2">
                  <Badge className="border-status-success/40 bg-status-success/10 text-status-success">
                    presentes: {lastIntake.present.length}
                  </Badge>
                  <Badge className="border-status-critical/40 bg-status-critical/10 text-status-critical">
                    faltantes: {lastIntake.missing.length}
                  </Badge>
                </div>
                <p className="mt-3 text-xs text-on-surface-variant">
                  Faltantes: {(lastIntake.missing || []).join(", ") || "ninguno"}
                </p>
              </div>
            )}
          </form>

          <section className="rounded-lg border border-outline-variant/20 bg-surface-container p-4">
            <h3 className="text-lg font-semibold text-on-surface">Checklist (pasos)</h3>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {(onboarding?.template_steps || []).map((step) => (
                <div key={step.id} className="rounded-md border border-outline-variant/20 bg-surface-elevated p-3">
                  <p className="text-sm font-semibold text-on-surface">{step.label}</p>
                  <p className="mt-1 text-xs text-on-surface-variant">{step.description}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
