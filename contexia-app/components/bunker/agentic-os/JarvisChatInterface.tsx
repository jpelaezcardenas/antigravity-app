"use client";

import { useRef, useState } from "react";
import { VoiceToggle } from "./VoiceToggle";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface JarvisChatInterfaceProps {
  withVoice?: boolean;
}

export function JarvisChatInterface({ withVoice = false }: JarvisChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: "user", text: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // SSE streaming via fetch
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
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  return (
    <div className="flex flex-col h-[420px] bg-surface-elevated rounded-xl border border-outline-variant/20 overflow-hidden">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {messages.length === 0 && (
          <p className="text-on-surface-variant text-sm text-center mt-8">
            Escríbele a Jarvis — tu asistente Contexia
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
            {msg.text || (loading && msg.role === "assistant" ? "▋" : "")}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
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
          placeholder="Pregúntale algo a Jarvis..."
          disabled={loading}
          className="flex-1 bg-transparent text-sm text-white placeholder:text-on-surface-variant outline-none py-1"
        />
        {withVoice && (
          <VoiceToggle onTranscript={(t) => sendMessage(t)} disabled={loading} />
        )}
        <button
          type="button"
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || loading}
          className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 text-primary flex items-center justify-center hover:bg-primary/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <span className="material-symbols-outlined text-[16px]">send</span>
        </button>
      </div>
    </div>
  );
}
