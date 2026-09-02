"use client";

import { useEffect, useState } from "react";
import { jarvisClient } from "@/lib/jarvis-client";

interface HermesStatus {
  online: boolean;
  url: string;
  uptime_seconds?: number;
}

export function HermesStatusCard() {
  const [status, setStatus] = useState<HermesStatus | null>(null);
  const [loadingState, setLoadingState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const data = await jarvisClient.status();
        setStatus(data);
        setLoadingState("ready");
      } catch {
        setLoadingState("error");
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColor = status?.online
    ? "text-status-success"
    : "text-status-warning";

  const statusLabel = status?.online ? "En línea" : "Desconectado";

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        Estado Hermes
      </span>

      {loadingState === "loading" && (
        <div className="h-20 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border border-on-surface-variant border-t-on-surface" />
        </div>
      )}

      {loadingState === "error" && (
        <div className="text-on-surface-variant text-sm">
          No se pudo conectar al gateway
        </div>
      )}

      {loadingState === "ready" && status && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${status.online ? "bg-status-success" : "bg-status-warning"}`} />
            <span className={`text-sm font-medium ${statusColor}`}>
              {statusLabel}
            </span>
          </div>

          <div className="flex flex-col gap-1 text-xs">
            <span className="text-on-surface-variant">
              Gateway:
            </span>
            <span className="font-mono text-on-surface break-all">
              {status.url || "—"}
            </span>
          </div>

          {status.uptime_seconds !== undefined && (
            <div className="flex flex-col gap-1 text-xs">
              <span className="text-on-surface-variant">Uptime:</span>
              <span className="text-on-surface">
                {formatUptime(status.uptime_seconds)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}
