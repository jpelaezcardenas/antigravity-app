"use client";

import { useState } from "react";
import { jarvisClient } from "@/lib/jarvis-client";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export function JarvisChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await jarvisClient.chat(input);
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-response`,
        role: "assistant",
        content: response.message || "Sin respuesta",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: "assistant",
        content: "Hubo un error al procesar tu mensaje. Intenta de nuevo.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3 h-96">
      <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        Chat con Jarvis
      </span>

      <div className="flex-1 overflow-y-auto flex flex-col gap-3 mb-3">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-on-surface-variant text-sm">
            <p>Inicia una conversación con Jarvis</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                msg.role === "user"
                  ? "bg-primary text-on-primary"
                  : "bg-surface-container text-on-surface"
              }`}
            >
              <p>{msg.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-surface-container text-on-surface px-3 py-2 rounded-lg">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-on-surface animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 rounded-full bg-on-surface animate-bounce" style={{ animationDelay: "100ms" }} />
                <div className="w-2 h-2 rounded-full bg-on-surface animate-bounce" style={{ animationDelay: "200ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="text-xs text-status-warning">
          {error}
        </div>
      )}

      <form onSubmit={handleSendMessage} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pregunta a Jarvis..."
          disabled={isLoading}
          className="flex-1 bg-surface border border-outline-variant rounded-lg px-3 py-2 text-sm text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
