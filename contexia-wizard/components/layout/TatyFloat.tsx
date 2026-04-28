"use client";
import React, { useState, useEffect } from "react";
import Image from "next/image";

/**
 * TatyFloat Component
 * Floating WhatsApp contact button with premium glassmorphism.
 */
export default function TatyFloat() {
  const [showBubble, setShowBubble] = useState(false);

  useEffect(() => {
    // Show bubble after 3.5 seconds
    const timer = setTimeout(() => {
      // Only show if user hasn't closed it in this session (optional, keeping it simple for now)
      setShowBubble(true);
    }, 3500);
    return () => clearTimeout(timer);
  }, []);

  const WA_URL =
    "https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría";

  return (
    <div className="taty-float">
      {showBubble && (
        <div className="taty-bubble animate-fadeInRight">
          <p style={{ margin: 0 }}>¿Tienes dudas con el Audit? ¡Hablemos! 👋</p>
          <button onClick={() => setShowBubble(false)} className="taty-bubble-close">&times;</button>
        </div>
      )}
      
      <a
        href={WA_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="taty-btn animate-pulse-subtle"
        aria-label="Hablar con Taty por WhatsApp"
        title="Hablar con Taty — Tu Amiga Contadora 24/7"
      >
        <Image
          src="https://www.contexia.online/assets/img/profiles/tatiana_full.png"
          alt="Taty"
          width={64}
          height={64}
          className="taty-avatar"
          unoptimized
        />
        <div className="taty-status" />
      </a>
    </div>
  );
}
