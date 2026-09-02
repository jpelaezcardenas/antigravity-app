"use client";

import { useEffect, useRef, useState } from "react";

interface VoiceToggleProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

// Web Speech API types — not in lib.dom by default in all TS versions
type AnySpeechRecognition = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function getSpeechRecognitionConstructor(): (new () => AnySpeechRecognition) | null {
  if (typeof window === "undefined") return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const w = window as any;
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function VoiceToggle({ onTranscript, disabled = false }: VoiceToggleProps) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<AnySpeechRecognition | null>(null);

  useEffect(() => {
    setSupported(getSpeechRecognitionConstructor() !== null);
  }, []);

  if (!supported) return null;

  function toggleListening() {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const SR = getSpeechRecognitionConstructor();
    if (!SR) return;

    const recognition = new SR();
    recognition.lang = "es-CO";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
    };

    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      disabled={disabled}
      aria-label={listening ? "Detener grabación" : "Hablar con Jarvis"}
      className={[
        "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all",
        listening
          ? "bg-red-500/20 border border-red-400 text-red-400 shadow-[0_0_12px_rgba(239,68,68,0.4)] animate-pulse"
          : "bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20",
        disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer",
      ].join(" ")}
    >
      <span className="material-symbols-outlined text-[20px]">
        {listening ? "stop" : "mic"}
      </span>
    </button>
  );
}
