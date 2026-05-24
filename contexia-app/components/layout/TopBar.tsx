"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export function TopBar() {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const router = useRouter();

  const [user, setUser] = useState(() => {
    if (typeof window !== "undefined") {
      const userData = localStorage.getItem("cx_user");
      return userData ? JSON.parse(userData) : null;
    }
    return null;
  });

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("cx_user");
    router.push("/auth");
  };

  const handleSwitchAccount = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("cx_user");
    router.push("/auth?mode=switch");
  };

  return (
    <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10 shadow-[0_0_20px_rgba(45,212,191,0.05)]">
      <div className="flex justify-between items-center px-container-margin-mobile md:px-container-margin-desktop h-touch-target-min">
        {/* Logo / Branding */}
        <Link href="/app/overview" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-md bg-surface-variant flex items-center justify-center overflow-hidden border border-white/10 shrink-0 group-hover:border-primary/30 transition-colors">
            <img src="/logo.png" alt="Contexia" className="w-full h-full object-cover" />
          </div>
          <h1 className="hidden sm:block font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg font-bold text-primary-container">
            Contexia
          </h1>
        </Link>

        {/* User Menu */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-variant/50 transition-colors"
          >
            <div className="flex flex-col items-end gap-0">
              <span className="font-body-md text-body-md text-on-surface line-clamp-1">
                {user?.company_name || "Usuario"}
              </span>
              <span className="font-body-sm text-body-sm text-on-surface-variant text-xs">
                {user?.email || "No autenticado"}
              </span>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-container font-bold text-sm">
              {user?.company_name?.[0]?.toUpperCase() || "U"}
            </div>
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-surface border border-outline-variant/20 rounded-lg shadow-lg p-2 z-50">
              {/* User Info */}
              <div className="px-3 py-2 border-b border-outline-variant/10 mb-2">
                <p className="font-title-md text-title-md text-on-surface">
                  {user?.company_name || "Usuario"}
                </p>
                <p className="font-body-sm text-body-sm text-on-surface-variant text-xs">
                  {user?.email || "No disponible"}
                </p>
              </div>

              {/* Menu Items */}
              <button
                type="button"
                onClick={() => {
                  router.push("/app/settings");
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded hover:bg-surface-variant/50 transition-colors font-body-md text-body-md text-on-surface mb-1"
              >
                ⚙️ Configuración
              </button>

              <button
                type="button"
                onClick={() => {
                  router.push("/app/help");
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded hover:bg-surface-variant/50 transition-colors font-body-md text-body-md text-on-surface mb-2"
              >
                ❓ Ayuda
              </button>

              <div className="border-t border-outline-variant/10 pt-2 mb-2" />

              {/* Switch Account */}
              <button
                type="button"
                onClick={handleSwitchAccount}
                className="w-full text-left px-3 py-2 rounded hover:bg-primary/10 transition-colors font-body-md text-body-md text-primary-container mb-1"
              >
                🔄 Cambiar Empresa
              </button>

              {/* Logout */}
              <button
                type="button"
                onClick={handleLogout}
                className="w-full text-left px-3 py-2 rounded hover:bg-status-error/10 transition-colors font-body-md text-body-md text-status-error"
              >
                🚪 Cerrar Sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
