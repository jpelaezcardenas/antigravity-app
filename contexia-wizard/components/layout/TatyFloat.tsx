"use client";
import React, { useState, useEffect } from "react";
import Image from "next/image";

/**
 * TatyFloat Component
 * Floating WhatsApp contact button — compact, non-intrusive.
 */
export default function TatyFloat() {
  const [showBubble, setShowBubble] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowBubble(true), 5000);
    return () => clearTimeout(timer);
  }, []);

  const WA_URL =
    "https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría";

  return (
    <div className="taty-float" style={{ bottom: "1.25rem", right: "1.25rem" }}>
      {showBubble && (
        <div className="taty-bubble" style={{ maxWidth: "180px", fontSize: "0.75rem", padding: "0.625rem 0.875rem" }}>
          <p style={{ margin: 0 }}>¿Dudas? ¡Hablemos! 👋</p>
          <button onClick={() => setShowBubble(false)} className="taty-bubble-close">&times;</button>
        </div>
      )}
      
      <a
        href={WA_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="taty-btn"
        aria-label="Hablar con Taty por WhatsApp"
        title="Hablar con Taty — Tu Amiga Contadora 24/7"
      >
        <Image
          src="https://www.contexia.online/assets/img/profiles/tatiana_full.png"
          alt="Taty"
          width={48}
          height={48}
          className="taty-avatar"
          style={{ borderRadius: "50%", objectFit: "cover" }}
          unoptimized
        />
        <div className="taty-status" style={{ width: "0.5rem", height: "0.5rem", bottom: "0.15rem", right: "0.15rem" }} />
      </a>
    </div>
  );
}
