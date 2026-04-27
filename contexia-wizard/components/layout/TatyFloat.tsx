"use client";
import Image from "next/image";

const WA_URL =
  "https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría";

export default function TatyFloat() {
  return (
    <a
      href={WA_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="taty-float"
      aria-label="Hablar con Taty por WhatsApp"
      title="Hablar con Taty — Tu Amiga Contadora 24/7"
    >
      {/* Badge online */}
      <div style={{ position: "relative", display: "inline-block" }}>
        <Image
          src="https://www.contexia.online/assets/img/profiles/tatiana_full.png"
          alt="Taty — Tu Amiga Contadora"
          width={64}
          height={64}
          style={{ borderRadius: "50%", display: "block", border: "3px solid #fff", boxShadow: "0 4px 12px rgba(0,0,0,0.2)" }}
          unoptimized
        />
        <span
          style={{
            position: "absolute",
            bottom: 2,
            right: 2,
            width: "14px",
            height: "14px",
            background: "#22c55e",
            borderRadius: "50%",
            border: "2px solid #fff",
          }}
        />
      </div>
      {/* Label */}
      <div
        style={{
          position: "absolute",
          bottom: "70px",
          right: 0,
          background: "#0a2540",
          color: "#fff",
          fontSize: "0.75rem",
          fontWeight: 600,
          padding: "0.375rem 0.625rem",
          borderRadius: "8px",
          whiteSpace: "nowrap",
          boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
          pointerEvents: "none",
        }}
      >
        Taty 24/7 — En línea
      </div>
    </a>
  );
}
