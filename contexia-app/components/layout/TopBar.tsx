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
    <header className="w-full z-50 bg-bg-obsidian/80 backdrop-blur-xl border-b border-outline-variant/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] flex flex-col justify-center items-center h-32 md:h-40 px-container-margin-mobile md:px-container-margin-desktop relative">
      
      {showBack && (
        <button
          type="button"
          aria-label="Volver"
          onClick={() => router.back()}
          className="absolute left-container-margin-mobile top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-primary transition-colors flex items-center justify-center h-10 w-10"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
      )}

      <Link href="/app/overview" className="flex items-center justify-center w-full mb-2 hover:opacity-90 transition-opacity">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo.png"
          alt="Contexia"
          className="h-12 md:h-16 w-auto object-contain drop-shadow-[0_0_15px_rgba(45,212,191,0.2)]"
        />
      </Link>
      
      <h1 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg font-bold text-primary-container flex items-center text-center">
        {title}
        {titleSecondary && (
          <span className="ml-2 font-title-md text-title-md text-on-surface hidden sm:inline-block">
            | {titleSecondary}
          </span>
        )}
      </h1>

      {showAlerts && !showBack && (
        <button
          type="button"
          aria-label="Alertas"
          className="absolute right-container-margin-mobile top-1/2 -translate-y-1/2 w-touch-target-min h-touch-target-min flex items-center justify-center text-on-surface-variant hover:text-status-warning active:scale-95 transition-all"
        >
          <span className="material-symbols-outlined text-[24px]">
            emergency
          </span>
        </button>
      )}
    </header>
  );
}
