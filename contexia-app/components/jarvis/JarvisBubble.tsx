"use client";

import { useEffect, useRef, useState } from "react";
import { fetchTenantMe, type TenantMeSnapshot } from "@/lib/api-client";
import { VoiceToggle } from "@/components/bunker/agentic-os/VoiceToggle";

// JARVIS header badge — implemented from the design handoff
// (design_handoff_jarvos_header_circle/README.md, 2026-09-14, high-fidelity). Colors, stroke
// widths and animation timings below are the handoff's FINAL values, not placeholders — do not
// re-tune them without a new handoff. Geometry is defined once at viewBox 0 0 88 88 and scaled
// via the container's CSS size (72px mobile / 88px desktop), which scales every stroke/halo
// proportionally for free — this is why there is only one size-dependent number below (the
// container's own width/height), not a full per-breakpoint config table.
//
// Three-layer anatomy: (1) outer segmented ring ("contorno", #2DD4BF, the only layer that
// glows), (2) fine radial-tick ring ("anillo intermedio", #8B5CF6), (3) flat dark core
// (#111D2E) holding only the Contexia mark. A separate text label (company name) sits below
// the badge, outside the ring/halo bounds — never inside the core per the handoff.
//
// Note: the SSE-parsing body of sendMessage() below intentionally mirrors
// components/bunker/agentic-os/JarvisChatInterface.tsx rather than sharing a hook — see that
// component's history (commit 4933f0a). If a third chat surface appears, extract a shared hook.

type Visualizer = "idle" | "pensando" | "respondiendo";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface JarvisBubbleProps {
  /** Only controls the badge's rendered diameter — positioning is the parent's job.
   * 128 (mobile header) / 156 (desktop header, bumped twice 2026-09-15 for more header
   * presence: handoff's original 72/88 → 96/120 → 128/156) / 96 (2026-09-15 round 3 — the
   * desktop header instance moved into DesktopSidebar.tsx, below its nav items, at this
   * smaller size to fit the sidebar's own width instead of the header's). */
  size: 48 | 96 | 128 | 156;
  /** Where the chat panel opens relative to on desktop (`md:`) — mobile positioning is
   * identical either way. "header" (default) centers it under a header-hosted badge, used by
   * ClientTopBar in both places that still render one there. "sidebar" opens it beside
   * DesktopSidebar instead, for the instance that lives there now. */
  panelAnchor?: "header" | "sidebar";
  /** Caption below the "JARVIS · Activo" status line, e.g. "Toca a JARVIS para consultar tu
   * liquidez". Founder-provided redesign (2026-09-18) — replaces the old tenant-name label
   * (redundant once every page started showing the tenant name itself in its own header) with
   * JARVIS's own identity + live status, plus this per-page hint about what to ask it.
   * Defaults to a generic hint; pass a page-specific one where it adds value. */
  helperText?: string;
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

export function JarvisBubble({
  size,
  panelAnchor = "header",
  helperText = "Toca a JARVIS para consultar tu liquidez",
}: JarvisBubbleProps) {
  const [loaded, setLoaded] = useState(false);
  const [tenant, setTenant] = useState<TenantMeSnapshot | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [visualizer, setVisualizer] = useState<Visualizer>("idle");
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
        // Fail silent — same "never alarm for identity" idiom as TenantInfoCard. The badge
        // still renders (2026-09-14: it's never hidden), just falls back to "CONTEXIA"/locked.
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

  // Status label (2026-09-18 redesign): "JARVIS" + a live status word, replacing the old
  // tenant-name label — every page now shows its own tenant name in its own header, so a
  // second copy under the badge was redundant (that's what `hideLabel` used to paper over).
  // This is more useful anyway: it tells the user whether JARVIS is actually reachable on
  // their plan, not just whose account they're in.
  // "Inactivo", not "No disponible": the status sits inside the core (56/88 of the diameter)
  // and the longer word clipped at the circle's edges at every size — verified 2026-09-18.
  const statusLabel = hasJarvisChat ? "Activo" : "Inactivo";

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

  if (!loaded) return null;

  const px = `${size}px`;
  // Inner content must stay inside the dark core (r=28 of the 88 viewBox → 56/88 of the
  // diameter), not the full button box — otherwise the text under the pin would sit on top of
  // the rings. Everything inside scales off `size` so the 2026-09-18 layout (pin / JARVIS /
  // status, stacked) reads the same at every diameter.
  // Core is r=38.5 of the 88 viewBox → 77/88 of the diameter (2026-09-18 composition).
  const coreInset = Math.round((size * (1 - 77 / 88)) / 2);
  // 48 = the floating-button variant on non-Pulso screens (founder: "en las demas queda...
  // tirado a la izquierda como boton flotante"): pin only, no name/status inside, no caption.
  const compact = size <= 48;
  const pinPx = Math.round(size * (compact ? 0.45 : 0.24));
  const namePx = Math.max(8, Math.round(size * 0.09));
  const statusPx = Math.max(7, Math.round(size * 0.065));

  return (
    // gap-4 (2026-09-18): the rebuilt composition keeps every ring inside the 88 viewBox
    // (outer dotted ring r=43), so the caption no longer needs the old gap-8 clearance.
    <div className="flex flex-col items-center gap-4">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Cerrar JARVIS" : "Abrir JARVIS"}
        title={!hasJarvisChat ? "JARVIS no disponible" : undefined}
        className={[
          "group relative flex-shrink-0 rounded-full transition-transform duration-150",
          "hover:scale-105 active:scale-[0.94]",
          "focus-visible:outline-none focus-visible:[box-shadow:0_0_0_3px_#0F172A,0_0_0_6px_#fff]",
        ].join(" ")}
        style={{ width: px, height: px }}
      >
        {/* Harmonic wrapper — constant, slow scale+float motion so the badge always reads as
            "alive" (sinking on press is a separate, additional cue via the button's own
            active:scale above, not the only motion). Runs on its own element so it never
            fights the button's hover/press transform — nested transforms compose cleanly.
            "No disponible" grayscale now lives HERE (rings/halo only) instead of on the whole
            button — founder feedback 2026-09-16: the Contexia mark must stay at full original
            color on every plan (freemium/starter included), only the rings gray out. */}
        <div className="absolute inset-0 motion-safe:[animation:jarvis-harmonic_5.2s_ease-in-out_infinite]">
          {/* Halo — the only glowing layer, always breathing at idle, tenser on hover */}
          {hasJarvisChat && (
          <span
            className="absolute rounded-full pointer-events-none motion-safe:[animation:jarvis-breathe_4s_ease-in-out_infinite] group-hover:opacity-50 group-hover:[animation:none] transition-opacity duration-150"
            style={{
              // Formula-based for the same reason as labelMaxWidth above (ratio ~0.18 matches
              // the prior 22/128 and 28/156 hardcoded values).
              inset: `-${Math.round(size * 0.18)}px`,
              background: "radial-gradient(circle, rgba(45,212,191,.45), transparent 70%)",
              filter: "blur(8px)",
            }}
          />
          )}

        <svg viewBox="0 0 88 88" className="absolute inset-0 w-full h-full overflow-visible">
          <defs>
            {/* Real bloom (feGaussianBlur, not just a CSS-blurred backdrop span) for the two
                teal rings — this is what makes them read as incandescent/glowing rather than
                flat strokes. `id` is size-suffixed so the mobile/desktop instances (both
                mounted at once, toggled by Tailwind breakpoint classes) never collide. */}
            <filter id={`jarvis-glow-${size}`} x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="1.6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* 2026-09-18 — composition rebuilt to match the founder's reference image exactly
              ("usa exactamente el mismo circulo de esta imagen... hablo de su composicion"),
              replacing the previous five-ring J.A.R.V.I.S. HUD stack. Three layers only:
              (1) a faint dotted outer ring, (2) one thin solid glowing ring, (3) a dark core
              that fills the interior right up to that ring — no empty gap between ring and
              core, and no radial-tick / segmented / purple layers. */}

          {/* (1) Dotted outer belt — state-colored (founder, 2026-09-18: "el mismo patron del
              ring intermitente... gris inactivo, y en activo un cinturon magenta adicional"):
              gray when JARVIS isn't in the plan, the app's violet accent when it is. Slow spin
              keeps it alive either way. */}
          <circle
            cx="44"
            cy="44"
            r="43"
            fill="none"
            stroke={hasJarvisChat ? "#8B5CF6" : "#64748B"}
            strokeOpacity={hasJarvisChat ? 0.7 : 0.4}
            strokeWidth="1.2"
            strokeDasharray="1.5 4"
            style={{ transformOrigin: "44px 44px" }}
            className="motion-safe:[animation:jarvis-slow-spin_34s_linear_infinite]"
          />

          {/* (3) The core is NOT drawn here — see the content div after this wrapper. It lives
              outside the grayscale/brightness filter on purpose, so its fill stays exactly the
              page background in every state (founder, 2026-09-18: "el interior del circulo
              igual al resto, no negro"; same call as 2026-09-15 "debe ser igual al resto"). */}

          {/* (2) The one solid ring, thin + glowing, hugging the core. Hover brightens it;
              "procesando" swaps it for the amber sweep below. */}
          <circle
            cx="44"
            cy="44"
            r="38.5"
            fill="none"
            strokeWidth="2"
            filter={hasJarvisChat ? `url(#jarvis-glow-${size})` : undefined}
            className={`transition-colors duration-150 ${
              !hasJarvisChat
                ? "stroke-[#64748B]/60"
                : busy
                  ? "stroke-[#F59E0B]/30"
                  : "stroke-[#2DD4BF] group-hover:stroke-[#5CE8D8]"
            }`}
          />
          {busy && (
            <circle
              cx="44"
              cy="44"
              r="38.5"
              fill="none"
              stroke="#F59E0B"
              strokeWidth="2"
              strokeDasharray={`${(34 / 360) * (2 * Math.PI * 38.5)} ${2 * Math.PI * 38.5}`}
              transform="rotate(-90 44 44)"
              className="motion-safe:[animation:jarvis-process_1.6s_linear_infinite] motion-reduce:opacity-70"
            />
          )}
        </svg>
        </div>
        {/* /jarvis-harmonic wrapper — mark + status dot stay outside it, perfectly still, so the
            ID mark and status color read is never in motion, only the rings/halo around it. */}

        {/* Core content — 2026-09-18 redesign (founder-provided reference): the pin mark on
            top, "JARVIS" under it, then the live status, ALL inside the core (founder:
            "adentro del circulo poner Activo debajo del pin"). Bounded by `coreInset` so
            nothing spills onto the rings. Only the helper caption lives outside, below. */}
        <div
          className="absolute rounded-full overflow-hidden flex flex-col items-center justify-center bg-bg-obsidian"
          // +1 viewBox unit so this fill meets the ring stroke's inner edge (stroke 2 centered on
          // r=38.5 → inner edge r=37.5) without covering it.
          style={{ inset: `${coreInset + Math.round(size / 88)}px` }}
        >
          {open ? (
            <span className="material-symbols-outlined text-white text-[24px]">close</span>
          ) : (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/assets/img/jarvis_mark.png"
                alt="Jarvis"
                className="object-contain"
                style={{ width: pinPx, height: pinPx }}
              />
              {!compact && (
                <>
                  <span
                    className="text-primary font-bold uppercase leading-none mt-1"
                    style={{ fontSize: namePx, letterSpacing: "0.08em" }}
                  >
                    JARVIS
                  </span>
                  <span className="flex items-center gap-1 leading-none mt-1">
                    <span
                      className={`rounded-full ${hasJarvisChat ? "bg-primary" : "bg-on-surface-variant/50"}`}
                      style={{ width: statusPx * 0.7, height: statusPx * 0.7 }}
                    />
                    <span
                      className="text-on-surface-variant uppercase"
                      style={{ fontSize: statusPx, letterSpacing: "0.06em" }}
                    >
                      {statusLabel}
                    </span>
                  </span>
                </>
              )}
            </>
          )}
        </div>

      </button>

      {/* Helper caption — the only text outside the ring (founder: "poner el texto abajo: toca
          JARVIS para consultar tu liquidez"), per-page customizable via `helperText`. Hidden when
          JARVIS isn't in the plan — inviting a tap that would only show a lock is misleading. */}
      {hasJarvisChat && !compact && (
        <p
          className="text-[12px] text-on-surface-variant/80 text-center"
          style={{ maxWidth: `${Math.round(size * 2.2)}px` }}
        >
          {helperText}
        </p>
      )}

      {open && (
        <div
          className={[
            "fixed z-40 bg-surface-elevated border border-outline-variant/40 rounded-2xl shadow-2xl flex flex-col overflow-hidden left-4 right-4 top-[250px] h-[420px]",
            panelAnchor === "sidebar"
              ? // Opens beside DesktopSidebar (w-56) rather than centered under a header —
                // there's no badge in the header to center under on this layout anymore.
                "md:left-60 md:right-auto md:top-24 md:bottom-6 md:h-auto md:w-80 md:translate-x-0"
              : "md:left-1/2 md:right-auto md:-translate-x-1/2 md:top-[290px] md:w-full md:max-w-sm",
          ].join(" ")}
        >
          <div className="px-4 py-3 border-b border-outline-variant/20 flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{
                backgroundColor: busy ? "#F59E0B" : "#2DD4BF",
              }}
            />
            <p className="text-sm font-semibold text-white flex-1">JARVIS</p>
            {busy && (
              <span className="text-[10px] text-on-surface-variant uppercase tracking-wide">
                {visualizer === "pensando" ? "pensando..." : "respondiendo..."}
              </span>
            )}
          </div>

          {!hasJarvisChat ? (
            // A simple Jarvis for freemium/starter is planned but not built yet — the real
            // backend gate (has_feature(plan_tier, "jarvis_chat") in
            // jarvis_endpoints.py::jarvis_chat) still 403s these tenants today. "Coming soon",
            // not "upgrade to unlock" — don't oversell a paywall for something just unbuilt.
            <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6 text-center">
              <span className="material-symbols-outlined text-primary text-[40px]">bolt</span>
              <p className="text-white font-semibold text-sm">JARVIS para tu plan está en camino</p>
              <p className="text-on-surface-variant text-xs">
                Estamos construyendo una versión de JARVIS para tu plan. Pronto vas a poder
                usarla desde aquí.
              </p>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
                {messages.length === 0 && (
                  <p className="text-on-surface-variant text-sm text-center mt-8">
                    Pregúntale algo a JARVIS
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
                  placeholder="Escríbele a JARVIS..."
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
            </>
          )}
        </div>
      )}
    </div>
  );
}
