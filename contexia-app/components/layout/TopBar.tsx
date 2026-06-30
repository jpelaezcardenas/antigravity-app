"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

interface TopBarProps {
  title?: string;
  titleSecondary?: string;
  showBack?: boolean;
  showAlerts?: boolean;
}

export function TopBar({
  title = "Contexia",
  titleSecondary,
  showBack = false,
  showAlerts = true,
}: TopBarProps) {
  const router = useRouter();

  return (
    <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-primary/20 shadow-[0_0_20px_rgba(45,212,191,0.1)] flex justify-between items-center px-container-margin-mobile md:px-container-margin-desktop h-touch-target-min">
      <div className="flex items-center gap-3">
        {showBack ? (
          <button
            type="button"
            aria-label="Volver"
            onClick={() => router.back()}
            className="text-on-surface-variant hover:text-primary transition-colors flex items-center justify-center h-10 w-10"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
        ) : (
          <Link
            href="/app/overview"
            className="w-8 h-8 rounded-md bg-surface-variant flex items-center justify-center overflow-hidden border border-primary/30 shrink-0 shadow-[0_0_12px_rgba(45,212,191,0.2)]"
            aria-label="Contexia — Inicio"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo.png"
              alt="Contexia"
              className="w-full h-full object-cover"
            />
          </Link>
        )}
        <h1 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg font-bold text-primary flex items-center">
          {title}
          {titleSecondary && (
            <span className="ml-2 font-title-md text-title-md text-on-surface hidden sm:block">
              | {titleSecondary}
            </span>
          )}
        </h1>
      </div>

      {showBack ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src="/logo.png"
          alt="Contexia"
          className="h-8 w-auto object-contain mr-2"
        />
      ) : (
        showAlerts && (
          <button
            type="button"
            aria-label="Alertas"
            className="w-touch-target-min h-touch-target-min flex items-center justify-center text-on-surface-variant hover:opacity-80 active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined text-[24px]">
              emergency
            </span>
          </button>
        )
      )}
    </header>
  );
}
