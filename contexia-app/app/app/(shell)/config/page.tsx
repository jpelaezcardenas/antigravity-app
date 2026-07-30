"use client";

import { useState } from "react";

interface NotificationToggle {
  id: string;
  label: string;
  description: string;
  defaultOn: boolean;
}

const NOTIFICATIONS: NotificationToggle[] = [
  {
    id: "dian",
    label: "Avisos de la DIAN",
    description: "Te avisamos antes de cada vencimiento",
    defaultOn: true,
  },
  {
    id: "cash",
    label: "Avisos de tu plata",
    description: "Cuando tu caja se ponga apretada",
    defaultOn: true,
  },
  {
    id: "taty",
    label: "Consejos de Taty",
    description: "Tu amiga contadora te manda tips útiles",
    defaultOn: true,
  },
  {
    id: "biometric",
    label: "Huella o cara",
    description: "Entra sin escribir contraseña",
    defaultOn: false,
  },
];

export default function ConfigPage() {
  const [toggles, setToggles] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(NOTIFICATIONS.map((n) => [n.id, n.defaultOn])),
  );

  const handleToggle = (id: string) => {
    setToggles((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="px-container-margin-mobile md:px-container-margin-desktop max-w-3xl mx-auto flex flex-col gap-6 w-full mt-2 pb-12">
      <section className="flex flex-col gap-1">
        <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-white">
          Tu cuenta
        </h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Ajusta cómo te avisa Taty y maneja tu acceso
        </p>
      </section>

      <section className="bg-surface-elevated rounded-xl border border-primary/20 p-5 flex items-center gap-4 shadow-[0_0_20px_rgba(45,212,191,0.08)]">
        <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-primary to-[#8B5CF6] flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(45,212,191,0.3)]">
          <span className="material-symbols-outlined text-white text-[28px]">
            store
          </span>
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <p className="font-title-md text-title-md text-white truncate">
            Mi Empresa
          </p>
          <p
            className="text-[10px] text-primary font-bold uppercase tracking-widest"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Plan Starter · Activo
          </p>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h3
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest px-1"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Avisos
        </h3>
        <div className="flex flex-col gap-2">
          {NOTIFICATIONS.map((notif) => (
            <button
              key={notif.id}
              type="button"
              onClick={() => handleToggle(notif.id)}
              className="bg-surface-elevated rounded-xl border border-white/10 p-4 flex items-center gap-4 hover:border-primary/30 transition-all text-left"
            >
              <div className="flex-1 min-w-0">
                <p className="font-body-md text-body-md text-white font-semibold">
                  {notif.label}
                </p>
                <p className="font-body-md text-[12px] text-on-surface-variant mt-0.5">
                  {notif.description}
                </p>
              </div>
              <div
                className={`relative w-12 h-7 rounded-full transition-colors flex-shrink-0 ${
                  toggles[notif.id] ? "bg-primary" : "bg-white/10"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-6 h-6 rounded-full bg-white shadow-md transition-transform ${
                    toggles[notif.id] ? "translate-x-5" : "translate-x-0.5"
                  }`}
                />
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h3
          className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest px-1"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Ayuda
        </h3>
        <div className="flex flex-col gap-2">
          <a
            href="https://wa.me/573018948151?text=Hola%20Taty%2C%20necesito%20ayuda%20con%20la%20app"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-surface-elevated rounded-xl border border-white/10 p-4 flex items-center gap-3 hover:border-primary/30 transition-all"
          >
            <span className="material-symbols-outlined text-primary">chat</span>
            <div className="flex-1">
              <p className="font-body-md text-body-md text-white font-semibold">
                Hablar con Taty
              </p>
              <p className="font-body-md text-[12px] text-on-surface-variant">
                Tu amiga contadora por WhatsApp · 24/7
              </p>
            </div>
            <span className="material-symbols-outlined text-on-surface-variant">
              chevron_right
            </span>
          </a>
          <a
            href="/landing.html"
            className="bg-surface-elevated rounded-xl border border-white/10 p-4 flex items-center gap-3 hover:border-primary/30 transition-all"
          >
            <span className="material-symbols-outlined text-[#8B5CF6]">
              help_outline
            </span>
            <div className="flex-1">
              <p className="font-body-md text-body-md text-white font-semibold">
                ¿Qué es Contexia?
              </p>
              <p className="font-body-md text-[12px] text-on-surface-variant">
                Conoce todo lo que hace por ti
              </p>
            </div>
            <span className="material-symbols-outlined text-on-surface-variant">
              chevron_right
            </span>
          </a>
        </div>
      </section>

      <section className="flex flex-col gap-3 mt-2">
        <a
          href="/logout"
          className="bg-status-critical/10 hover:bg-status-critical/20 border border-status-critical/30 rounded-xl p-4 flex items-center justify-center gap-2 transition-all"
        >
          <span className="material-symbols-outlined text-status-critical">
            logout
          </span>
          <span className="text-status-critical font-bold">Cerrar sesión</span>
        </a>
        <p className="text-center text-[10px] text-on-surface-variant/60 mt-2">
          Contexia · GPS Financiero · v1.0
        </p>
      </section>
    </div>
  );
}
