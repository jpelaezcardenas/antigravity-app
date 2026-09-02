"use client";

import { useEffect, useState } from "react";
import { jarvisClient, type HermesStatusResponse } from "@/lib/jarvis-client";

type CardState = "loading" | "online" | "offline" | "error";

export function HermesStatusCard() {
  const [state, setState] = useState<CardState>("loading");
  const [data, setData] = useState<HermesStatusResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    jarvisClient
      .status()
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setState(res.online ? "online" : "offline");
      })
      .catch(() => {
        if (cancelled) return;
        setState("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const dot =
    state === "online"
      ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]"
      : state === "loading"
        ? "bg-white/20 animate-pulse"
        : "bg-red-400";

  const label =
    state === "loading"
      ? "Verificando..."
      : state === "online"
        ? "Hermes · En línea"
        : "Hermes · Sin conexión";

  const sub =
    state === "online" && data?.uptime_seconds
      ? `Uptime ${Math.floor(data.uptime_seconds / 60)} min`
      : state === "online" && data?.url
        ? data.url.replace("https://", "").slice(0, 30)
        : state === "error" || state === "offline"
          ? "Gateway no alcanzable"
          : "";

  return (
    <div className="bg-surface-elevated rounded-xl border border-outline-variant/20 p-4 flex items-center gap-3">
      <div className={`w-3 h-3 rounded-full flex-shrink-0 ${dot}`} />
      <div className="flex flex-col min-w-0">
        <p className="font-body-md text-body-md text-white text-sm font-semibold truncate">
          {label}
        </p>
        {sub && (
          <p className="text-[11px] text-on-surface-variant truncate">{sub}</p>
        )}
      </div>
    </div>
  );
}
