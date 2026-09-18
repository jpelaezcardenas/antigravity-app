"use client";

import { useEffect, useState } from "react";

/**
 * Per-device opt-in to preview the -v2 pilot routes through normal navigation
 * (BottomNav/DesktopSidebar), instead of only reaching them by typing the
 * exact -v2 URL. Founder-only convenience while -v2 stays unlinked from
 * production navigation for everyone else — never touches other tenants'
 * devices, never affects the default BottomNav/DesktopSidebar targets.
 */
const KEY = "cx-v2-preview";
const EVENT = "cx-v2-preview-changed";

export function getV2Preview(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}

export function setV2Preview(enabled: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, enabled ? "1" : "0");
  } catch {
    // localStorage unavailable (private mode, etc.) — preview just won't persist.
  }
  window.dispatchEvent(new CustomEvent(EVENT, { detail: enabled }));
}

export function useV2Preview(): boolean {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    setEnabled(getV2Preview());
    const onChange = (e: Event) => setEnabled((e as CustomEvent<boolean>).detail);
    const onStorage = (e: StorageEvent) => {
      if (e.key === KEY) setEnabled(e.newValue === "1");
    };
    window.addEventListener(EVENT, onChange);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(EVENT, onChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  return enabled;
}

const V2_ROUTE_MAP: Record<string, string> = {
  "/app/overview": "/app/overview-v2",
  "/app/fiscal": "/app/fiscal-v2",
  "/app/radar": "/app/radar-v2",
  "/app/patrimonio": "/app/patrimonio-v2",
};

/** Maps a production nav path to its -v2 pilot equivalent when preview is on. Routes
 * without a -v2 pilot yet (e.g. /app/config) pass through unchanged. */
export function toV2Path(path: string, previewEnabled: boolean): string {
  if (!previewEnabled) return path;
  return V2_ROUTE_MAP[path] ?? path;
}
