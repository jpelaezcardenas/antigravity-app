"use client";

import { useEffect, useRef, useState } from "react";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";
import { VoiceToggle } from "@/components/bunker/agentic-os/VoiceToggle";

// D4/D5 (hermes-jarvis-contexia, re-scoped 2026-09-14 per founder request): the single
// Jarvis entry point for already-won clients lives IN the header — replacing the old
// "Taty" WhatsApp card and the (unwired) hamburger menu, not floating separately. Gated
// the same way as the Búnker's AgenticOsSection (jarvis_chat: admin or growth/enterprise;
// jarvis_voice: admin or enterprise). NOT the full-screen "circuit board" visualizer —
// just a small state dot (D5).
//
// Two instances are rendered by ClientTopBar (desktop + mobile), matching the pre-existing
// pattern for the Taty card it replaces — each has independent state; only the visible one
// (via responsive classes) can ever be opened.
//
// Note: the SSE-parsing body of sendMessage() below intentionally mirrors
// components/bunker/agentic-os/JarvisChatInterface.tsx rather than sharing a hook —
// that component already shipped to production (commit 4933f0a) and this task didn't
// need to touch it. If a third chat surface appears, extract a shared hook then.

type VisualizerState = "idle" | "pensando" | "respondiendo";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface JarvisBubbleProps {
  /** Controls trigger sizing/placement — desktop sits inline in the header's right
   * cluster; mobile is centered like the Taty card it replaces. */
  variant: "desktop" | "mobile";
}

function readRoleFromJwt(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie
    .split("; ")
    .find((c) => c.startsWith("sb-access-token="));
  if (!match) return "";
  const token = match.split("=").slice(1).join("=");
  const parts = token.split(".");
  if (parts.length !== 3) return "";
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
    const appMeta = payload.app_metadata ?? {};
    const userMeta = payload.user_metadata ?? {};
    return String(
      appMeta.role ?? appMeta.account_role ?? userMeta.role ?? userMeta.account_role ?? ""
    ).toLowerCase();
  } catch {
    return "";
  }
}

const VISUALIZER_DOT: Record<VisualizerState, string> = {
  idle: "bg-white/30",
  pensando: "bg-amber-400 animate-pulse",
  respondiendo: "bg-primary animate-pulse",
};

const VISUALIZER_LABEL: Record<VisualizerState, string> = {
  idle: "",
  pensando: "pensando...",
  respondiendo: "respondiendo...",
};

export function JarvisBubble({ variant }: JarvisBubbleProps) {
  const [loaded, setLoaded] = useState(false);
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [visualizer, setVisualizer] = useState<VisualizerState>("idle");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const role = readRoleFromJwt();
    setIsAdmin(["admin", "superadmin", "contexia_admin"].includes(role));

    let cancelled = false;
    fetchTenantMe()
      .then((snapshot) => {
        if (cancelled) return;
        setTenant(snapshot);
      })
      .catch(() => {
        // Fail silent — same "never alarm for identity" idiom as TenantInfoCard.
        // The bubble simply stays hidden (see `loaded && hasJarvisChat` gate below).
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tier = tenant?.plan_tier ?? null;
  const hasJarvisChat = isAdmin || tier === "growth" || tier === "enterprise";
  const hasVoice = isAdmin || tier === "enterprise";
  const busy = visualizer !== "idle";

  async function sendMessage(text: string) {
    if (!text.trim() || busy) return;

    const userMsg: Message = { role: "user", text: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setVisualizer("pensando");

    const token =
      typeof localStorage !== "undefined" ? localStorage.getItem("token") : null;

    try {
      const res = await fetch("/api/v1/jarvis/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text.trim() }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`${res.status} ${res.statusText}`);
      }

      const assistantMsg: Message = { role: "assistant", text: "" };
      setMessages((prev) => [...prev, assistantMsg]);
      setVisualizer("respondiendo");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") break;
          try {
            const chunk = JSON.parse(payload) as { text?: string; error?: string };
            if (chunk.error) throw new Error(chunk.error);
            if (chunk.text) {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last.role === "assistant") {
                  next[next.length - 1] = { ...last, text: last.text + chunk.text };
                }
                return next;
              });
            }
          } catch {
            // malformed chunk — skip
          }
        }
      }
    } catch (err) {
      const errText = err instanceof Error ? err.message : "Error al contactar a Jarvis";
      setMessages((prev) => [...prev, { role: "assistant", text: `⚠️ ${errText}` }]);
    } finally {
      setVisualizer("idle");
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  if (!loaded || !hasJarvisChat) return null;

  // The button shows the official Contexia mark (assets/img/jarvis_mark.png, cropped from
  // logo_official.png) — a dark/glass background so the mark's own gradient is what reads,
  // not a flat teal fill fighting it.
  const triggerClassName =
    variant === "desktop"
      ? "relative w-14 h-14 rounded-full bg-black/40 backdrop-blur-xl border border-primary/40 shadow-[0_4px_20px_rgba(45,212,191,0.35)] flex items-center justify-center hover:border-primary/70 transition-colors flex-shrink-0"
      : "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-14 h-14 rounded-full bg-black/40 backdrop-blur-xl border border-primary/40 shadow-[0_0_20px_rgba(45,212,191,0.35)] flex items-center justify-center hover:border-primary/70 transition-colors";

  const panelClassName =
    "fixed top-[112px] right-4 md:top-[92px] md:right-8 z-40 w-[calc(100vw-2rem)] max-w-sm h-[420px] bg-surface-elevated rounded-2xl border border-outline-variant/20 shadow-2xl flex flex-col overflow-hidden";

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Cerrar Jarvis" : "Abrir Jarvis"}
        className={triggerClassName}
      >
        <span
          className={`absolute w-3 h-3 rounded-full -top-0.5 -right-0.5 border-2 border-bg-obsidian z-10 ${VISUALIZER_DOT[visualizer]}`}
        />
        {open ? (
          <span className="material-symbols-outlined text-white text-[26px]">close</span>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src="/assets/img/jarvis_mark.png"
            alt="Jarvis"
            className="w-full h-full object-contain p-1.5"
          />
        )}
      </button>

      {open && (
        <div className={panelClassName}>
          <div className="px-4 py-3 border-b border-outline-variant/20 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${VISUALIZER_DOT[visualizer]}`} />
            <p className="text-sm font-semibold text-white flex-1">Jarvis</p>
            {visualizer !== "idle" && (
              <span className="text-[10px] text-on-surface-variant uppercase tracking-wide">
                {VISUALIZER_LABEL[visualizer]}
              </span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
            {messages.length === 0 && (
              <p className="text-on-surface-variant text-sm text-center mt-8">
                Pregúntale algo a Jarvis
              </p>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={[
                  "max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed whitespace-pre-wrap",
                  msg.role === "user"
                    ? "self-end bg-primary/20 text-white border border-primary/30"
                    : "self-start bg-white/5 text-white/90 border border-outline-variant/10",
                ].join(" ")}
              >
                {msg.text || (visualizer === "respondiendo" && msg.role === "assistant" ? "▋" : "")}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-outline-variant/20 px-3 py-2 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(input);
                }
              }}
              placeholder="Escríbele a Jarvis..."
              disabled={busy}
              className="flex-1 bg-transparent text-sm text-white placeholder:text-on-surface-variant outline-none py-1"
            />
            {hasVoice && <VoiceToggle onTranscript={(t) => sendMessage(t)} disabled={busy} />}
            <button
              type="button"
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || busy}
              className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 text-primary flex items-center justify-center hover:bg-primary/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[16px]">send</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
