"use client";

import { useState, useRef, useEffect } from "react";
import { askTaty, type TatyAskResponse, type TatyAskRequest } from "@/lib/services/api";
import type { TatyUIStatus } from "@/lib/types/taty";

interface TatyViewProps {
  company_id?: string;
  onResponse?: (response: TatyAskResponse) => void;
}

export function TatyView({ company_id = "ctx-001", onResponse }: TatyViewProps) {
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<TatyUIStatus>("idle");
  const [response, setResponse] = useState<TatyAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) return;

    setStatus("loading");
    setError(null);

    try {
      const request: TatyAskRequest = {
        company_id,
        question: question.trim(),
        channel: "dashboard",
      };

      const result = await askTaty(request);
      setResponse(result);
      setStatus("success");
      setQuestion(""); // Clear input after success
      onResponse?.(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error desconocido";
      setError(errorMessage);
      setStatus("error");
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-6">
      {/* Input Section */}
      <form onSubmit={handleAsk} className="flex flex-col gap-3">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Pregunta a Taty sobre fiscal, impuestos, régimen, UVT..."
            disabled={status === "loading"}
            className="w-full px-4 py-3 pr-12 rounded-lg border border-outline bg-surface-elevated text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          />
          <button
            type="submit"
            disabled={status === "loading" || !question.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-on-surface-variant hover:text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <span className="material-symbols-outlined text-xl">
              {status === "loading" ? "hourglass_empty" : "send"}
            </span>
          </button>
        </div>
        <p className="text-label-sm text-on-surface-variant">
          Taty responde preguntas sobre DIAN, impuestos, régimen tributario y más.
        </p>
      </form>

      {/* Error State */}
      {error && status === "error" && (
        <div className="p-4 rounded-lg bg-error/10 border border-error/30 flex items-start gap-3">
          <span className="material-symbols-outlined text-error mt-0.5">error</span>
          <div className="flex-1">
            <h4 className="font-semibold text-error text-sm">Error</h4>
            <p className="text-error/80 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Response Section */}
      {response && status === "success" && (
        <div className="flex flex-col gap-4">
          {/* Main Answer Card */}
          <div className="p-5 rounded-xl bg-surface-elevated border border-outline flex flex-col gap-4">
            {/* Header with Latency and Confidence */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-ai-narrative-tint">
                  support_agent
                </span>
                <span className="text-sm font-semibold text-on-surface">
                  Respuesta de Taty
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-on-surface-variant">
                <span>⏱️ {response.latency_ms}ms</span>
                <span>
                  📊 {Math.round(response.confidence * 100)}% confianza
                </span>
              </div>
            </div>

            {/* Answer Text */}
            <div className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">
              {response.answer}
            </div>

            {/* Escalation Badge */}
            {response.requires_human_review && (
              <div className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-warning/10 border border-warning/30 w-fit">
                <span className="material-symbols-outlined text-warning text-lg">
                  warning
                </span>
                <span className="text-xs font-semibold text-warning">
                  Requiere revisión de CFO
                </span>
              </div>
            )}
          </div>

          {/* Citations */}
          {response.citations.length > 0 && (
            <div className="p-4 rounded-xl bg-surface-variant/50 border border-outline/30 flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-on-surface-variant text-lg">
                  library_books
                </span>
                <h4 className="font-semibold text-sm text-on-surface">
                  Fuentes citadas
                </h4>
              </div>
              <div className="flex flex-col gap-2">
                {response.citations.map((citation, idx) => (
                  <div key={idx} className="text-xs text-on-surface-variant">
                    <p className="font-semibold text-on-surface">
                      {citation.source}
                    </p>
                    <p className="mt-1 italic">{citation.fragment}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setResponse(null);
                setStatus("idle");
                inputRef.current?.focus();
              }}
              className="flex-1 px-4 py-2 rounded-lg border border-outline text-sm font-semibold text-on-surface hover:bg-surface-variant transition-colors"
            >
              Nueva pregunta
            </button>
            {response.requires_human_review && (
              <button
                className="flex-1 px-4 py-2 rounded-lg bg-primary text-on-primary text-sm font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-base">
                  person_outline
                </span>
                Contactar CFO
              </button>
            )}
          </div>
        </div>
      )}

      {/* Loading State */}
      {status === "loading" && (
        <div className="p-6 rounded-xl bg-surface-elevated border border-outline flex flex-col items-center justify-center gap-3">
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 rounded-full border-2 border-primary/20"></div>
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin"></div>
          </div>
          <p className="text-sm text-on-surface-variant">
            Taty está procesando tu pregunta...
          </p>
        </div>
      )}
    </div>
  );
}
