"use client";

import { useState, useRef, useEffect } from "react";
import { jarvisClient } from "@/lib/jarvis-client";

type SpeechRecognitionEvent = Event & {
  results?: SpeechRecognitionResultList;
};

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
  length: number;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

type SpeechRecognition = {
  new (): {
    start: () => void;
    stop: () => void;
    abort: () => void;
    onstart?: (event: Event) => void;
    onresult?: (event: SpeechRecognitionEvent) => void;
    onerror?: (event: Event) => void;
    onend?: (event: Event) => void;
    continuous: boolean;
    interimResults: boolean;
    lang: string;
  };
};

export function VoiceToggle() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "es-ES";

      recognition.onstart = () => {
        setIsListening(true);
        setTranscript("");
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interim = "";
        for (let i = event.results!.length - 1; i >= 0; --i) {
          const transcript = event.results![i][0].transcript;
          if (event.results![i].isFinal) {
            interim += transcript + " ";
          }
        }
        setTranscript(interim);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = async () => {
        setIsListening(false);
        if (transcript.trim()) {
          setIsProcessing(true);
          try {
            await jarvisClient.chat(transcript);
            setTranscript("");
          } catch (err) {
            console.error("Error sending voice message:", err);
          } finally {
            setIsProcessing(false);
          }
        }
      };

      recognitionRef.current = recognition;
    }
  }, [transcript]);

  const handleVoiceToggle = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
    }
  };

  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-3">
      <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wide">
        Modo Voz
      </span>

      <div className="flex flex-col gap-3">
        <button
          onClick={handleVoiceToggle}
          disabled={isProcessing}
          className={`w-full py-3 rounded-lg font-medium transition-all ${
            isListening
              ? "bg-status-error text-on-primary animate-pulse"
              : "bg-primary text-on-primary hover:opacity-90"
          } disabled:opacity-50`}
        >
          {isListening
            ? "Escuchando..."
            : isProcessing
              ? "Procesando..."
              : "Presiona para hablar"}
        </button>

        {transcript && (
          <div className="bg-surface-container rounded-lg p-3 text-sm text-on-surface">
            <p className="text-xs text-on-surface-variant mb-1">Transcripción:</p>
            <p>{transcript}</p>
          </div>
        )}

        <p className="text-xs text-on-surface-variant text-center">
          Habla en español para que Jarvis te entienda
        </p>
      </div>
    </div>
  );
}
