"use client";
import { isFeria, getFeriaConfig } from "@/lib/feriaConfig";

/**
 * FeriaBanner — Sticky banner showing event info when in feria mode
 * Shows "EN VIVO" indicator, event name, location, and date
 */
export default function FeriaBanner() {
  if (!isFeria()) return null;
  const config = getFeriaConfig()!;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, rgba(249,115,22,0.15) 0%, rgba(168,85,247,0.15) 50%, rgba(45,212,191,0.15) 100%)",
        borderBottom: "1px solid rgba(249,115,22,0.3)",
        padding: "0.625rem 1rem",
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 60,
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
    >
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "1rem",
          flexWrap: "wrap",
          fontSize: "0.8125rem",
        }}
      >
        {/* Live indicator */}
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.375rem",
            background: "rgba(239,68,68,0.2)",
            color: "#f87171",
            fontWeight: 800,
            fontSize: "0.6875rem",
            padding: "0.25rem 0.625rem",
            borderRadius: "999px",
            border: "1px solid rgba(239,68,68,0.3)",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: "#ef4444",
              animation: "pulse-subtle 1.5s ease-in-out infinite",
              boxShadow: "0 0 8px rgba(239,68,68,0.6)",
            }}
          />
          En vivo
        </span>

        {/* Event info */}
        <span style={{ color: "#f8fafc", fontWeight: 700 }}>
          {config.nombre}
        </span>
        <span style={{ color: "#94a3b8" }}>·</span>
        <span style={{ color: "#94a3b8" }}>
          📍 {config.lugar}
        </span>
        <span style={{ color: "#94a3b8" }}>·</span>
        <span style={{ color: "#94a3b8" }}>
          📅 {config.fecha}
        </span>
      </div>
    </div>
  );
}
