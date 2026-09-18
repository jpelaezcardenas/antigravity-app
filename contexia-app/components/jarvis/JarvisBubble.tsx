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
  size: 96 | 128 | 156;
  /** Where the chat panel opens relative to on desktop (`md:`) — mobile positioning is
   * identical either way. "header" (default) centers it under a header-hosted badge, used by
   * ClientTopBar in both places that still render one there. "sidebar" opens it beside
   * DesktopSidebar instead, for the instance that lives there now. */
  panelAnchor?: "header" | "sidebar";
  /** Hides the company-name label under the badge. Default false (unchanged everywhere
   * else). Set true where that name is already shown elsewhere on the page — e.g.
   * JarvisFloatingBadgeV2 on the -v2 pilots, where PulsoHeroV2/each page's own header
   * already renders the tenant name, making this second label redundant (founder,
   * 2026-09-18: "elimina esto debajo del badge de jarvis"). */
  hideLabel?: boolean;
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

export function JarvisBubble({ size, panelAnchor = "header", hideLabel = false }: JarvisBubbleProps) {
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

  // Company label: each client sees their own name (e.g. "FEREZ", "CODIGO520") instead of the
  // generic fallback — per the handoff, this is a separate label below the badge, never text
  // baked into the core. Full name always available via the native `title` tooltip.
  // 2026-09-16 (founder request): fallback reads "CONTEXIA.ONLINE" (the domain), not "CONTEXIA".
  const fullLabel = tenant?.legal_name?.trim() || "Contexia.online";
  const displayLabel = fullLabel.toUpperCase();

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
  // Formula-based (was a hardcoded per-size ternary) so a third size (96, sidebar) didn't need
  // its own branch — ratio matches the original handoff's 96px/120px → 160px/220px pairing.
  const labelMaxWidth = `${Math.round(size * 1.8)}px`;

  return (
    // gap bumped 2026-09-15 (from 1.5) — the outer decorative rings (r up to 58 of the 88
    // viewBox) extend ~25px past the button's own box on every side via overflow-visible, so a
    // tight gap let the ring's bottom arc visually collide with the company label below it.
    <div className="flex flex-col items-center gap-8">
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
        <div
          className={[
            "absolute inset-0 motion-safe:[animation:jarvis-harmonic_5.2s_ease-in-out_infinite]",
            !hasJarvisChat ? "[filter:grayscale(1)_brightness(.75)]" : "",
          ].join(" ")}
        >
          {/* Halo — the only glowing layer, always breathing at idle, tenser on hover */}
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

          {/* Outermost — faint depth ring, barely-there context (matches the far/background
              ring in the J.A.R.V.I.S. reference), never competing with anything inside it. */}
          <circle
            cx="44"
            cy="44"
            r="58"
            fill="none"
            stroke="#2DD4BF"
            strokeOpacity="0.15"
            strokeWidth="1"
            strokeDasharray="1 8"
            style={{ transformOrigin: "44px 44px" }}
            className="motion-safe:[animation:jarvis-slow-spin_34s_linear_infinite]"
          />

          {/* Thick incandescent segmented ring (founder request, 2026-09-14/15 — "anillo mas
              grueso por segmentos de tono mas incandescente sobresaliente" from the J.A.R.V.I.S.
              reference). Lives strictly OUTSIDE the handoff's own contorno (r=41) so it never
              touches the three spec layers below — added presence, zero interference. Brighter
              and thicker than the spec ring on purpose: this is the "sobresaliente" layer. */}
          <circle
            cx="44"
            cy="44"
            r="52"
            fill="none"
            stroke="#99F6E4"
            strokeOpacity="0.9"
            strokeWidth="5"
            strokeDasharray="13 5"
            transform="rotate(-90 44 44)"
            filter={`url(#jarvis-glow-${size})`}
            style={{ transformOrigin: "44px 44px" }}
            className="motion-safe:[animation:jarvis-slow-spin-reverse_24s_linear_infinite]"
          />

          {/* Thin accent ring in the gap between the incandescent ring and the spec contorno —
              adds one more layer of depth without ever sitting inside the handoff's own
              anatomy (that gap, between r=33 and r=41, is deliberate per the design — nothing
              goes there). */}
          <circle
            cx="44"
            cy="44"
            r="45.5"
            fill="none"
            stroke="#5CE8D8"
            strokeOpacity="0.45"
            strokeWidth="1"
            strokeDasharray="1 5"
            style={{ transformOrigin: "44px 44px" }}
            className="motion-safe:[animation:jarvis-slow-spin_22s_linear_infinite]"
          />

          {/* Middle ring — fine radial ticks, secondary color, never competes with the outer
              ring. EXACT handoff spec (r=33, #8B5CF6, width 1.5, opacity .4, dasharray "1.5
              12") — only addition is its own slow rotation (29s, shares no short common period
              with the 34s/24s/22s rings above) so nothing ever visually phase-locks. */}
          <circle
            cx="44"
            cy="44"
            r="33"
            fill="none"
            stroke="#8B5CF6"
            strokeOpacity="0.4"
            strokeWidth="1.5"
            strokeDasharray="1.5 12"
            style={{ transformOrigin: "44px 44px" }}
            className="motion-safe:[animation:jarvis-slow-spin_29s_linear_infinite]"
          />

          {/* Outer ring ("contorno") — EXACT handoff spec (r=41, width 3.5, dasharray "11 4",
              #2DD4BF). Rotated -90deg so the pattern starts at 12 o'clock. Color/opacity swap
              for hover/procesando states; now also carries the real glow filter. */}
          <circle
            cx="44"
            cy="44"
            r="41"
            fill="none"
            strokeWidth="3.5"
            strokeDasharray="11 4"
            transform="rotate(-90 44 44)"
            filter={`url(#jarvis-glow-${size})`}
            className={`transition-colors duration-150 ${
              busy ? "stroke-[#F59E0B]/30" : "stroke-[#2DD4BF] group-hover:stroke-[#5CE8D8]"
            }`}
          />
          {busy && (
            <circle
              cx="44"
              cy="44"
              r="41"
              fill="none"
              stroke="#F59E0B"
              strokeWidth="3.5"
              strokeDasharray={`${(34 / 360) * (2 * Math.PI * 41)} ${2 * Math.PI * 41}`}
              transform="rotate(-90 44 44)"
              className="motion-safe:[animation:jarvis-process_1.6s_linear_infinite] motion-reduce:opacity-70"
            />
          )}

          {/* Core — EXACT handoff spec: flat dark surface (r=28, #111D2E), only the Contexia
              mark lives inside. */}
          {/* Fill matches the page/header background exactly (#0F172A, `bg-bg-obsidian`) —
              was the handoff's own #111D2E, a close-but-different navy that read as a visibly
              blacker "hole" against the rest of the UI, especially once the "no disponible"
              grayscale/dim filter (see the button's className above) desaturated both
              differently. Founder feedback 2026-09-15: "debe ser igual al resto". */}
          <circle cx="44" cy="44" r="28" fill="#0F172A" stroke="rgba(255,255,255,.08)" />
        </svg>
        </div>
        {/* /jarvis-harmonic wrapper — mark + status dot stay outside it, perfectly still, so the
            ID mark and status color read is never in motion, only the rings/halo around it. */}

        <div
          className="absolute rounded-full overflow-hidden flex items-center justify-center"
          style={{ inset: "16px" }}
        >
          {open ? (
            <span className="material-symbols-outlined text-white text-[24px]">close</span>
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src="/assets/img/jarvis_mark.png"
              alt="Jarvis"
              className="object-contain"
              style={{
                width: "45%",
                height: "45%",
              }}
            />
          )}
        </div>

      </button>

      {/* Company label — separate element, outside the ring/halo bounds, never inside the core.
          2026-09-16 (founder request): font normalized to `font-label-caps` (Inter) — same
          token DesktopSidebar's nav labels use, right above this in the sidebar. The handoff's
          original spec called for Rajdhani here specifically, but the founder's later,
          explicit, repeated feedback ("no cambies de estilo de letra... normaliza estas letras
          como el resto de la app") overrides that for this element. Hidden via `hideLabel` where
          the page already shows the tenant name elsewhere (see JarvisFloatingBadgeV2). */}
      {!hideLabel && (
        <p
          title={fullLabel}
          className="font-label-caps text-label-caps text-on-surface font-semibold uppercase truncate text-center"
          style={{
            letterSpacing: "0.05em",
            maxWidth: labelMaxWidth,
          }}
        >
          {displayLabel}
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
