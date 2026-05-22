"use client";

import { useState } from "react";

export function TatyActionBar() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");

  const handleSendMessage = () => {
    if (message.trim()) {
      console.log("Mensaje enviado a Taty:", message);
      setMessage("");
      setTimeout(() => {
        alert('Taty responderá: "Entendido. Evaluando opciones de ajuste..."');
      }, 300);
    }
  };

  return (
    <>
      {/* Sticky CTA Button */}
      <div className="fixed bottom-0 w-full p-4 bg-gradient-to-t from-bg-obsidian via-bg-obsidian to-transparent z-40 pb-safe">
        <button
          onClick={() => setIsOpen(true)}
          className="w-full max-w-3xl mx-auto h-touch-target-min bg-primary text-on-primary font-title-md text-title-md rounded-xl flex items-center justify-center gap-2 hover:bg-primary-fixed transition-colors shadow-[0_0_20px_rgba(45,212,191,0.2)]"
        >
          <span
            className="material-symbols-outlined"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            chat
          </span>
          Chat con Taty para Ajustes
        </button>
      </div>

      {/* Modal Drawer Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Drawer Panel */}
      <div
        className={`fixed bottom-0 right-0 w-full max-w-md bg-surface-elevated border-l border-white/10 z-50 transform transition-transform duration-300 flex flex-col max-h-screen rounded-tl-xl ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/5">
          <h3 className="font-title-md text-title-md text-primary-container">
            Ajustes con Taty
          </h3>
          <button
            onClick={() => setIsOpen(false)}
            className="text-on-surface-variant hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-3">
          {/* Mock AI message */}
          <div className="flex gap-2 items-start">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
              <span
                className="material-symbols-outlined text-primary text-[18px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                smart_toy
              </span>
            </div>
            <div className="bg-surface-container rounded-lg p-3 max-w-xs">
              <p className="font-body-md text-body-md text-on-surface">
                Hola, soy Taty. ¿Qué ajustes necesitas hacer en tu estructura
                financiera?
              </p>
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-white/5 p-4 flex flex-col gap-2 bg-surface">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe tu necesidad..."
            className="w-full bg-surface-container border border-outline-variant/30 rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:ring-1 focus:ring-primary/50 resize-none"
            rows={3}
          />
          <button
            onClick={handleSendMessage}
            disabled={!message.trim()}
            className="w-full h-touch-target-min bg-primary text-on-primary font-title-md text-title-md rounded-lg hover:bg-primary-fixed transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Enviar
          </button>
        </div>
      </div>
    </>
  );
}
