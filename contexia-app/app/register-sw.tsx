"use client";

import { useEffect } from "react";
import { registerServiceWorker } from "@/lib/sw-register";

/**
 * Componente que registra el Service Worker en el cliente
 * Se monta automáticamente desde el root layout
 */
export function RegisterSW() {
  useEffect(() => {
    registerServiceWorker();
  }, []);

  return null;
}
