"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

type Status = "PENDING" | "APPROVED" | "DECLINED" | "VOIDED" | "ERROR";

interface StatusResponse {
  reference: string;
  status: Status;
  paymentMethod: string | null;
  wompiTransactionId: string | null;
  finalAmountCop: number;
  customerEmail: string | null;
}

function formatCop(value: number): string {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 }).format(value);
}

export default function ConfirmacionPage() {
  const [params, setParams] = useState<{ reference: string | null }>({ reference: null });
  const [data, setData] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const u = new URL(window.location.href);
    const ref = u.searchParams.get("ref") || u.searchParams.get("reference");
    setParams({ reference: ref });
  }, []);

  useEffect(() => {
    if (!params.reference) return;
    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 60; // ~3 min @ 3s
    async function poll() {
      while (!cancelled && attempts < maxAttempts) {
        attempts++;
        try {
          const res = await fetch(`/wizard/api/payments/status/${encodeURIComponent(params.reference!)}`);
          if (res.ok) {
            const json = (await res.json()) as StatusResponse;
            if (cancelled) return;
            setData(json);
            if (json.status !== "PENDING") return;
          } else if (res.status === 404) {
            setError("No encontramos esta orden.");
            return;
          }
        } catch {
          // network blip; keep polling
        }
        await new Promise((r) => setTimeout(r, 3000));
      }
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, [params.reference]);

  const waLink = useMemo(() => {
    const ref = data?.reference || params.reference || "";
    const msg = encodeURIComponent(`Hola Taty, acabo de completar el pago de mi empresa. Orden ${ref}. Necesito confirmar los siguientes pasos.`);
    return `https://wa.me/573018948151?text=${msg}`;
  }, [data, params.reference]);

  if (!params.reference) {
    return (
      <Shell>
        <Card>
          <Title>Falta la referencia</Title>
          <p style={muted}>No recibimos el número de orden. Si pagaste, revisa tu correo o escríbele a Taty.</p>
          <WaButton href={waLink} />
        </Card>
      </Shell>
    );
  }

  if (error) {
    return (
      <Shell>
        <Card>
          <Title>Hmm…</Title>
          <p style={muted}>{error}</p>
          <WaButton href={waLink} />
        </Card>
      </Shell>
    );
  }

  if (!data || data.status === "PENDING") {
    return (
      <Shell>
        <Card>
          <Spinner />
          <Title>Confirmando tu pago…</Title>
          <p style={muted}>Esto toma unos segundos. No cierres esta ventana.</p>
          <Meta label="Orden" value={params.reference} />
        </Card>
      </Shell>
    );
  }

  if (data.status === "APPROVED") {
    return (
      <Shell>
        <Card success>
          <Badge ok>¡Pago aprobado!</Badge>
          <h1 style={{ fontFamily: "Orbitron, sans-serif", color: "#fff", fontSize: 28, fontWeight: 900, margin: "12px 0 6px" }}>
            ¡Listo! Tu empresa empieza a tomar forma 🚀
          </h1>
          <p style={muted}>Pagaste <strong style={{ color: "#fff" }}>{formatCop(data.finalAmountCop)}</strong> con {data.paymentMethod || "tu método"}. Taty te escribe por WhatsApp en minutos.</p>
          <div style={{ background: "rgba(45,212,191,0.08)", border: "1px solid rgba(45,212,191,0.3)", borderRadius: 14, padding: 16, marginTop: 18 }}>
            <Meta label="Número de orden" value={data.reference} mono />
            {data.wompiTransactionId && <Meta label="Transacción Wompi" value={data.wompiTransactionId} mono />}
            {data.customerEmail && <Meta label="Te enviamos correo a" value={data.customerEmail} />}
          </div>
          <WaButton href={waLink} />
          <Link href="/" style={tinyLink}>Volver al inicio</Link>
        </Card>
      </Shell>
    );
  }

  // DECLINED / VOIDED / ERROR
  return (
    <Shell>
      <Card error>
        <Badge error>Pago no completado</Badge>
        <Title>El cobro no se procesó</Title>
        <p style={muted}>Tu pago aparece como <strong>{data.status}</strong>. No te preocupes — no se descontó nada. Puedes intentar de nuevo desde el wizard.</p>
        <Meta label="Orden" value={data.reference} mono />
        <a href="/crear-empresa-wizard" style={{
          ...btnPrimary, background: "#8B5CF6", boxShadow: "0 0 24px rgba(139,92,246,0.4)",
        }}>Reintentar pago</a>
        <WaButton href={waLink} secondary />
      </Card>
    </Shell>
  );
}

/* ── presentational helpers ── */

const muted = { color: "#94a3b8", fontSize: 14, lineHeight: 1.6, margin: "0 0 8px" } as const;
const tinyLink = { color: "#94a3b8", fontSize: 11, textTransform: "uppercase" as const, letterSpacing: "0.1em", fontFamily: "Rajdhani, sans-serif", fontWeight: 700, marginTop: 12, textDecoration: "none" };
const btnPrimary = {
  display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8,
  background: "#25D366", color: "#fff", textDecoration: "none", fontWeight: 700,
  padding: "14px 24px", borderRadius: 12, marginTop: 16,
  boxShadow: "0 0 24px rgba(37,211,102,0.4)",
};

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main style={{ minHeight: "100vh", background: "#020617", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, fontFamily: "Inter, system-ui, sans-serif" }}>
      {children}
    </main>
  );
}

function Card({ children, success, error }: { children: React.ReactNode; success?: boolean; error?: boolean }) {
  const borderColor = success ? "rgba(45,212,191,0.4)" : error ? "rgba(239,68,68,0.4)" : "rgba(255,255,255,0.1)";
  const glow = success ? "0 0 60px rgba(45,212,191,0.25)" : error ? "0 0 60px rgba(239,68,68,0.18)" : "0 0 40px rgba(45,212,191,0.1)";
  return (
    <div style={{
      maxWidth: 520, width: "100%",
      background: "linear-gradient(135deg, rgba(45,212,191,0.08), rgba(139,92,246,0.08))",
      border: `1px solid ${borderColor}`,
      borderRadius: 24, padding: 32, backdropFilter: "blur(20px)",
      textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
      boxShadow: glow,
    }}>{children}</div>
  );
}

function Title({ children }: { children: React.ReactNode }) {
  return <h1 style={{ fontFamily: "Rajdhani, sans-serif", color: "#fff", fontSize: 24, fontWeight: 800, margin: "8px 0 4px" }}>{children}</h1>;
}

function Badge({ children, ok, error }: { children: React.ReactNode; ok?: boolean; error?: boolean }) {
  const bg = ok ? "rgba(34,197,94,0.15)" : error ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.06)";
  const fg = ok ? "#22C55E" : error ? "#ef4444" : "#94a3b8";
  return <span style={{ background: bg, color: fg, fontSize: 11, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", padding: "6px 14px", borderRadius: 999, fontFamily: "Rajdhani, sans-serif" }}>{children}</span>;
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, fontSize: 12, padding: "4px 0" }}>
      <span style={{ color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", fontFamily: "Rajdhani, sans-serif", fontWeight: 700 }}>{label}</span>
      <span style={{ color: "#fff", fontFamily: mono ? "JetBrains Mono, monospace" : undefined, fontSize: mono ? 11 : 13, fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ width: 48, height: 48, borderRadius: "50%", border: "3px solid rgba(45,212,191,0.2)", borderTopColor: "#2DD4BF", animation: "ctx-spin 0.9s linear infinite" }}>
      <style jsx global>{`@keyframes ctx-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function WaButton({ href, secondary }: { href: string; secondary?: boolean }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" style={{
      ...btnPrimary,
      background: secondary ? "rgba(37,211,102,0.15)" : "#25D366",
      color: secondary ? "#25D366" : "#fff",
      border: secondary ? "1px solid rgba(37,211,102,0.4)" : "none",
      boxShadow: secondary ? "none" : "0 0 24px rgba(37,211,102,0.4)",
    }}>📲 Escribir a Taty por WhatsApp</a>
  );
}
