"use client";
import { useState, useEffect } from "react";
import { useWizardStore, type AuditResult } from "@/lib/store";
import StepWrapper from "../StepWrapper";
import { formatCOP, formatMillones, compararRegimenes } from "@/lib/calculations";
import { detectarRiesgos, detectarOportunidades } from "@/lib/riskAnalysis";
import { calcularReadiness } from "@/lib/readinessScore";
import { ga4 } from "@/lib/ga4";
import { CheckCircle, AlertTriangle, XCircle, TrendingUp, Download, MessageCircle, Building2 } from "lucide-react";

// ─── CIIU 1090 Banner ────────────────────────────────────────
function Ciiu1090Banner() {
  useEffect(() => { ga4.ciiu1090BannerShown(); }, []);
  return (
    <div style={{
      background: "linear-gradient(135deg, var(--ctx-violet) 0%, #4f46e5 100%)",
      borderRadius: "16px",
      padding: "1.75rem",
      marginBottom: "2rem",
      display: "flex",
      gap: "1.25rem",
      alignItems: "flex-start",
      boxShadow: "0 15px 35px -10px rgba(124, 58, 237, 0.4)",
      border: "1px solid rgba(255,255,255,0.1)",
    }}>
      <span style={{ fontSize: "2rem", flexShrink: 0 }}>⚡</span>
      <div>
        <h4 className="font-orbitron" style={{ color: "#ffffff", fontWeight: 800, fontSize: "1rem", margin: "0 0 0.5rem", letterSpacing: "0.02em" }}>
          Atención CIIU 1090 — Elaboración de alimentos
        </h4>
        <p style={{ color: "rgba(255,255,255,0.8)", fontSize: "0.875rem", margin: "0 0 1rem", lineHeight: 1.6 }}>
          Tu actividad está sujeta a regulación del INVIMA y BPM.
          Antes de formalizar, verifica el certificado sanitario y el concepto de uso de suelos.
        </p>
        <a
          href="https://wa.me/573018948151?text=Hola%20Taty,%20tengo%20CIIU%201090%20y%20necesito%20orientación%20sobre%20INVIMA%20y%20BPM"
          target="_blank" rel="noopener noreferrer"
          className="ctx-btn-secondary"
          style={{
            fontSize: "0.8125rem",
            padding: "0.625rem 1.25rem",
            textDecoration: "none",
            display: "inline-flex",
          }}
          onClick={() => ga4.whatsappOpened()}
        >
          💬 Consultar especialista INVIMA/BPM
        </a>
      </div>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────

function ReadinessGauge({ score, band }: { score: number; band: "verde" | "ambar" | "rojo" }) {
  const color = band === "verde" ? "#16a34a" : band === "ambar" ? "#d97706" : "#dc2626";
  const radius = 70;
  const circumference = Math.PI * radius; // half circle
  const progress = (score / 100) * circumference;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
      <svg width="180" height="100" viewBox="0 0 180 100">
        {/* Background arc */}
        <path d="M 10 90 A 80 80 0 0 1 170 90" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="14" strokeLinecap="round" />
        {/* Progress arc */}
        <path
          d="M 10 90 A 80 80 0 0 1 170 90"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${(score / 100) * 251} 251`}
          style={{ transition: "stroke-dasharray 1s ease" }}
        />
        {/* Score text */}
        <text x="90" y="80" textAnchor="middle" fontSize="28" fontWeight="800" fill="white">{score}</text>
        <text x="90" y="96" textAnchor="middle" fontSize="11" fill="var(--ctx-text-muted)">/100</text>
      </svg>
    </div>
  );
}

function RiesgoCard({ riesgo }: { riesgo: any }) {
  const config: Record<string, { bg: string; border: string; color: string; icon: any; label: string }> = {
    CRÍTICO: { bg: "rgba(220, 38, 38, 0.1)", border: "rgba(220, 38, 38, 0.3)", color: "#ef4444", icon: XCircle, label: "CRÍTICO" },
    ALTO: { bg: "rgba(245, 158, 11, 0.1)", border: "rgba(245, 158, 11, 0.3)", color: "#f59e0b", icon: AlertTriangle, label: "ALTO" },
    MEDIO: { bg: "rgba(59, 130, 246, 0.1)", border: "rgba(59, 130, 246, 0.3)", color: "#3b82f6", icon: AlertTriangle, label: "MEDIO" },
    BAJO: { bg: "rgba(16, 185, 129, 0.1)", border: "rgba(16, 185, 129, 0.3)", color: "#10b981", icon: CheckCircle, label: "BAJO" },
  };
  const c = config[riesgo.nivel] || config.MEDIO;
  const Icon = c.icon;

  return (
    <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: "12px", padding: "1.25rem" }}>
      <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
        <Icon size={20} color={c.color} style={{ flexShrink: 0, marginTop: "2px" }} />
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "white", background: c.color, padding: "0.2rem 0.6rem", borderRadius: "999px" }}>{c.label}</span>
            <h4 className="font-orbitron" style={{ color: "white", fontWeight: 700, fontSize: "0.9375rem", margin: 0 }}>{riesgo.titulo}</h4>
          </div>
          <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.875rem", margin: "0 0 0.75rem", lineHeight: 1.6 }}>{riesgo.descripcion}</p>
          <p style={{ color: "white", fontSize: "0.875rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ color: "#10b981" }}>✓</span> {riesgo.accion}
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Main Step 8 Component ────────────────────────────────────

interface Props { onBack: () => void; }

export default function Step8Diagnostico({ onBack }: Props) {
  const store = useWizardStore();
  const [loading, setLoading] = useState(false);
  const [auditDone, setAuditDone] = useState(!!store.auditResult);
  const [emailInput, setEmailInput] = useState(store.paso1?.email || "");
  const [emailSent, setEmailSent] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);

  const executeAudit = async () => {
    setLoading(true);
    try {
      const ingresosAnuales = (store.paso4?.ingresos_mensuales || 0) * 12;
      const costosPct = store.paso4?.costos_pct || 50;
      const ciiu = store.paso2?.ciiu_principal || "4791";
      const ciudad = store.paso1?.ciudad || "Medellín";

      const comparativo = compararRegimenes(ingresosAnuales, costosPct, ciiu, ciudad);
      const riesgos = detectarRiesgos({
        ciiu_principal: ciiu,
        tipo_sociedad: store.paso2?.tipo_sociedad,
        ingresos_mensuales: store.paso4?.ingresos_mensuales,
        costos_pct: costosPct,
        tiene_ingresos_previos: store.paso4?.tiene_ingresos_previos,
        ha_declarado_renta: store.paso4?.ha_declarado_renta,
        tiene_contador: store.paso5?.tiene_contador,
        facturacion_electronica: store.paso5?.facturacion_electronica,
        empleados: store.paso6?.empleados,
        tiene_bpa: store.paso6?.tiene_bpa,
        tiene_ecommerce: store.paso7?.tiene_ecommerce,
      });
      const oportunidades = detectarOportunidades({
        ciiu_principal: ciiu,
        tipo_sociedad: store.paso2?.tipo_sociedad,
        tiene_ecommerce: store.paso7?.tiene_ecommerce,
        tiene_bpa: store.paso6?.tiene_bpa,
      }, ingresosAnuales, comparativo.ahorroPotencialAnual);
      const readiness = calcularReadiness({
        tiene_contador: store.paso5?.tiene_contador,
        facturacion_electronica: store.paso5?.facturacion_electronica,
        software_contable: store.paso7?.software_contable,
        tiene_ecommerce: store.paso7?.tiene_ecommerce,
        empleados: store.paso6?.empleados,
        ha_declarado_renta: store.paso4?.ha_declarado_renta,
        maneja_inventarios: store.paso5?.maneja_inventarios,
        tiene_bpa: store.paso6?.tiene_bpa,
      });

      const result: AuditResult = {
        recomendacion: comparativo.recomendacion,
        ingresosAnuales,
        costosTotales: comparativo.ordinario.costosTotales,
        utilidadBruta: comparativo.ordinario.utilidadBruta,
        margenPct: comparativo.ordinario.margenNeto,
        impuestoSimple: comparativo.simple.impuestoAnual,
        impuestoOrdinario: comparativo.ordinario.totalImpuestos,
        ahorroPotencial: comparativo.ahorroPotencialAnual,
        readinessScore: readiness.score,
        readinessBand: readiness.band,
        riesgos,
        oportunidades,
      };

      store.setAuditResult(result);
      // Track audit execution
      ga4.auditExecuted({
        regimen: result.recomendacion,
        readiness_score: result.readinessScore,
        riesgos_count: riesgos.length,
        ahorro_potencial: result.ahorroPotencial,
      });
      // Save to Supabase
      await fetch("/wizard/api/audit/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ leadId: store.leadId, result, paso1: store.paso1 }),
      });
      setAuditDone(true);
    } finally {
      setLoading(false);
    }
  };

  const sendEmail = async () => {
    setEmailLoading(true);
    try {
      await fetch("/wizard/api/audit/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailInput, leadId: store.leadId, result: store.auditResult, nombre: store.paso1?.nombre }),
      });
      setEmailSent(true);
      ga4.emailSent();
    } finally {
      setEmailLoading(false);
    }
  };

  const result = store.auditResult;

  if (!auditDone) {
    return (
      <StepWrapper
        step={8}
        headline="Tu diagnóstico Contexia"
        subheadline="Análisis tributario personalizado basado en tu información."
        onBack={onBack}
        isLastStep
      >
        <div style={{ textAlign: "center", padding: "4rem 1rem" }}>
          <div style={{ fontSize: "4rem", marginBottom: "1.5rem" }}>🔍</div>
          <h3 className="font-orbitron" style={{ fontSize: "1.5rem", fontWeight: 800, color: "white", marginBottom: "1rem", letterSpacing: "0.02em" }}>
            Todo listo para tu Shadow Audit
          </h3>
          <p style={{ color: "var(--ctx-text-muted)", fontSize: "1rem", maxWidth: "480px", margin: "0 auto 2.5rem", lineHeight: 1.6 }}>
            Analizaremos tu caso en segundos: Simple vs Ordinario, riesgos DIAN, oportunidades y tu plan de acción.
          </p>
          <button onClick={executeAudit} disabled={loading} className="ctx-btn-primary"
            style={{ fontSize: "1.125rem", padding: "1rem 3.5rem", borderRadius: "14px" }}>
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <span className="animate-spin" style={{ display: "inline-block", width: "22px", height: "22px", border: "3px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%" }} />
                Ejecutando análisis...
              </span>
            ) : "🔍 Ejecutar Shadow Audit"}
          </button>
          {loading && (
            <div style={{ marginTop: "2rem", color: "var(--ctx-text-muted)", fontSize: "0.875rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <p>Calculando regímenes tributarios...</p>
              <p>Identificando riesgos DIAN...</p>
              <p>Proyectando ahorros...</p>
            </div>
          )}
        </div>
      </StepWrapper>
    );
  }

  if (!result) return null;

  return (
    <StepWrapper
      step={8}
      headline="Tu diagnóstico Contexia"
      subheadline="Análisis tributario personalizado basado en tu información."
      onBack={onBack}
      isLastStep
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* CIIU 1090 special banner */}
        {store.paso2?.ciiu_principal === "1090" && <Ciiu1090Banner />}
        
        {/* A — Resumen ejecutivo */}
        <div style={{
          background: result.recomendacion === "simple" ? "rgba(16, 185, 129, 0.1)" : "rgba(59, 130, 246, 0.1)",
          border: `1px solid ${result.recomendacion === "simple" ? "rgba(16, 185, 129, 0.3)" : "rgba(59, 130, 246, 0.3)"}`,
          borderRadius: "16px", padding: "1.75rem",
        }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "1.5rem", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3 className="font-orbitron" style={{ fontWeight: 800, fontSize: "1.25rem", color: "white", margin: "0 0 0.5rem" }}>
                {store.paso2?.nombre_opcion1 || "Tu empresa"}
              </h3>
              <p style={{ color: "var(--ctx-text-muted)", fontSize: "0.9375rem", margin: 0 }}>
                Régimen recomendado:{" "}
                <strong style={{ color: result.recomendacion === "simple" ? "#10b981" : "#3b82f6" }}>
                  {result.recomendacion === "simple" ? "Régimen Simple" : "Régimen Ordinario"}
                </strong>
              </p>
            </div>
            <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#10b981" }}>{formatMillones(result.ahorroPotencial)}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--ctx-text-muted)", fontWeight: 600 }}>Ahorro potencial/año</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, color: result.readinessBand === "verde" ? "#10b981" : result.readinessBand === "ambar" ? "#f59e0b" : "#ef4444" }}>
                  {result.readinessScore}/100
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--ctx-text-muted)", fontWeight: 600 }}>Readiness Score</div>
              </div>
            </div>
          </div>
        </div>

        {/* B — Proyección financiera */}
        <div className="ctx-card">
          <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "1.125rem" }}>
            <TrendingUp size={18} className="text-teal-400" /> Proyección Financiera Anual
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "1rem" }}>
            {[
              { label: "Ingresos anuales", val: formatMillones(result.ingresosAnuales), color: "#10b981" },
              { label: "Costos totales", val: formatMillones(result.costosTotales), color: "#ef4444" },
              { label: "Utilidad bruta", val: formatMillones(result.utilidadBruta), color: "var(--ctx-violet)" },
              { label: "Margen neto", val: `${result.margenPct.toFixed(1)}%`, color: result.margenPct > 30 ? "#10b981" : "#f59e0b" },
            ].map((item) => (
              <div key={item.label} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "14px", padding: "1.25rem", textAlign: "center" }}>
                <div style={{ fontSize: "1.375rem", fontWeight: 800, color: item.color }}>{item.val}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--ctx-text-muted)", marginTop: "0.5rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", marginBottom: "1.25rem", fontSize: "1.125rem", letterSpacing: "0.02em" }}>Comparativo: Simple vs Ordinario</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
            {/* Simple */}
            <div style={{
              border: `1.5px solid ${result.recomendacion === "simple" ? "var(--ctx-teal)" : "rgba(255,255,255,0.1)"}`,
              borderRadius: "16px", padding: "1.5rem",
              background: result.recomendacion === "simple" ? "rgba(45, 212, 191, 0.05)" : "rgba(255,255,255,0.02)",
              transition: "all 0.3s ease",
            }}>
              {result.recomendacion === "simple" && (
                <div style={{ background: "var(--ctx-teal)", color: "#000", fontSize: "0.75rem", fontWeight: 800, padding: "0.3125rem 0.875rem", borderRadius: "999px", display: "inline-flex", marginBottom: "1rem" }}>
                  ⭐ RECOMENDADO
                </div>
              )}
              <h4 className="font-orbitron" style={{ fontWeight: 700, color: "white", marginBottom: "0.875rem", fontSize: "1rem" }}>Régimen Simple</h4>
              {result.impuestoSimple > 0 ? (
                <>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#10b981" }}>{formatMillones(result.impuestoSimple)}<span style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--ctx-text-muted)" }}> /año</span></div>
                  <div style={{ fontSize: "0.8125rem", color: "var(--ctx-text-muted)", marginTop: "0.75rem", lineHeight: 1.6 }}>
                    Incluye: Renta + ICA integrados · IVA aparte si aplica
                  </div>
                </>
              ) : (
                <p style={{ color: "#ef4444", fontSize: "0.875rem", fontWeight: 600 }}>❌ No aplica para tu nivel de ingresos</p>
              )}
            </div>
            {/* Ordinario */}
            <div style={{
              border: `1.5px solid ${result.recomendacion === "ordinario" ? "var(--ctx-violet)" : "rgba(255,255,255,0.1)"}`,
              borderRadius: "16px", padding: "1.5rem",
              background: result.recomendacion === "ordinario" ? "rgba(139, 92, 246, 0.05)" : "rgba(255,255,255,0.02)",
              transition: "all 0.3s ease",
            }}>
              {result.recomendacion === "ordinario" && (
                <div style={{ background: "var(--ctx-violet)", color: "#fff", fontSize: "0.75rem", fontWeight: 800, padding: "0.3125rem 0.875rem", borderRadius: "999px", display: "inline-flex", marginBottom: "1rem" }}>
                  ⭐ RECOMENDADO
                </div>
              )}
              <h4 className="font-orbitron" style={{ fontWeight: 700, color: "white", marginBottom: "0.875rem", fontSize: "1rem" }}>Régimen Ordinario</h4>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--ctx-violet)" }}>{formatMillones(result.impuestoOrdinario)}<span style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--ctx-text-muted)" }}>/año</span></div>
              <div style={{ fontSize: "0.8125rem", color: "var(--ctx-text-muted)", marginTop: "0.75rem", lineHeight: 1.6 }}>
                Renta 35% + IVA neto + ICA municipal
              </div>
            </div>
          </div>
          {result.ahorroPotencial > 0 && (
            <div style={{ marginTop: "1.25rem", background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "12px", padding: "1rem 1.5rem", display: "flex", alignItems: "center", gap: "1rem" }}>
              <span style={{ fontSize: "1.5rem" }}>💰</span>
              <span style={{ fontWeight: 700, color: "#10b981", fontSize: "0.9375rem" }}>
                Veredicto: Ahorras {formatMillones(result.ahorroPotencial)}/año eligiendo el régimen correcto
              </span>
            </div>
          )}
        </div>

        {/* D — Riesgos */}
        {result.riesgos.length > 0 && (
          <div>
            <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", marginBottom: "1.25rem", fontSize: "1.125rem" }}>
              ⚠️ Riesgos Identificados ({result.riesgos.length})
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {result.riesgos.map((r) => <RiesgoCard key={r.titulo} riesgo={r} />)}
            </div>
          </div>
        )}

        {/* E — Oportunidades */}
        {result.oportunidades.length > 0 && (
          <div>
            <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", marginBottom: "1.25rem", fontSize: "1.125rem" }}>💡 Oportunidades</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {result.oportunidades.map((o) => (
                <div key={o.titulo} style={{ background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "14px", padding: "1.25rem" }}>
                  <h4 className="font-orbitron" style={{ color: "#10b981", fontWeight: 700, margin: "0 0 0.5rem", fontSize: "0.9375rem" }}>{o.titulo}</h4>
                  <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.875rem", margin: 0, lineHeight: 1.6 }}>{o.descripcion}</p>
                  {o.impactoEstimado && <p style={{ color: "#10b981", fontSize: "0.875rem", fontWeight: 800, marginTop: "0.625rem" }}>{o.impactoEstimado}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* F — Plan 30-60-90 */}
        <div>
          <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", marginBottom: "1.5rem", fontSize: "1.125rem" }}>📅 Plan de Acción 30-60-90 Días</h3>
          {[
            { label: "Días 0-30 — Constitución legal", color: "var(--ctx-violet)", items: ["Verificación de nombre en RUES", "Redacción de estatutos SAS", "Radicación en Cámara de Comercio", "NIT + RUT con responsabilidades correctas", "Habilitación facturación electrónica DIAN", "Apertura cuenta bancaria empresarial"] },
            { label: "Días 30-60 — Cumplimiento sectorial", color: "#f59e0b", items: ["Concepto de uso de suelos", "Concepto sanitario municipal", "Inicio trámite registro ICA en SimplifICA (si aplica)", "Setup software contable (Siigo / Alegra)"] },
            { label: "Días 60-90 — Operación formalizada", color: "var(--ctx-teal)", items: ["Migración del establecimiento existente a la nueva SAS", "Primera declaración Régimen Simple", "Plan de contingencia regulatorio", "Capacitación BPMAA (si aplica)"] },
          ].map((fase) => (
            <div key={fase.label} style={{ marginBottom: "1.75rem", paddingLeft: "1.25rem", borderLeft: `2px solid ${fase.color}33` }}>
              <h4 className="font-orbitron" style={{ fontWeight: 800, color: fase.color, fontSize: "0.9375rem", marginBottom: "0.875rem" }}>{fase.label}</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.625rem" }}>
                {fase.items.map((item) => (
                  <li key={item} style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.875rem", color: "rgba(255,255,255,0.8)" }}>
                    <span style={{ width: "16px", height: "16px", border: `1.5px solid ${fase.color}66`, borderRadius: "4px", flexShrink: 0, display: "inline-block" }} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* G — Readiness Score */}
        <div className="ctx-glass" style={{ textAlign: "center", padding: "2rem" }}>
          <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", marginBottom: "1rem" }}>Readiness Score</h3>
          <ReadinessGauge score={result.readinessScore} band={result.readinessBand} />
          <p style={{ fontWeight: 800, fontSize: "1rem", color: result.readinessBand === "verde" ? "#10b981" : result.readinessBand === "ambar" ? "#f59e0b" : "#ef4444", marginTop: "1rem" }}>
            {result.readinessScore >= 80 ? "Listo para formalizar — Empieza ya" : result.readinessScore >= 50 ? "Requiere ajustes — Te acompañamos" : "Foundation building crítico — Paquete completo recomendado"}
          </p>
        </div>

        {/* Disclaimer */}
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "1.25rem" }}>
          <p style={{ fontSize: "0.8125rem", color: "var(--ctx-text-muted)", margin: 0, lineHeight: 1.7 }}>
            <strong style={{ color: "white" }}>Disclaimer legal:</strong> Este diagnóstico es una herramienta de orientación generada automáticamente. NO constituye asesoría legal, contable o tributaria formal. Las cifras son estimaciones basadas en normativa vigente y pueden variar al validar con tus números reales. La firma de declaraciones tributarias requiere Contador Público titulado.
          </p>
        </div>

        {/* H — CTAs */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <h3 className="font-orbitron" style={{ fontWeight: 800, color: "white", margin: "0.5rem 0 0", fontSize: "1.125rem" }}>¿Qué sigue?</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
            <a href="https://www.contexia.online/crear-empresa.html" className="ctx-btn-primary"
              style={{ textDecoration: "none", textAlign: "center", padding: "1.25rem", borderRadius: "16px", display: "flex", flexDirection: "column", gap: "0.5rem", height: "auto" }}
              onClick={() => ga4.ctaClicked("crear_empresa")}>
              <Building2 size={24} />
              <span style={{ fontWeight: 800 }}>Crear mi empresa</span>
              <span style={{ fontSize: "0.8125rem", opacity: 0.9, fontWeight: 500 }}>Paquetes desde $1.2M</span>
            </a>
            <a href="https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría"
              target="_blank" rel="noopener noreferrer" className="ctx-btn-secondary"
              style={{ textDecoration: "none", textAlign: "center", padding: "1.25rem", borderRadius: "16px", display: "flex", flexDirection: "column", gap: "0.5rem", height: "auto" }}
              onClick={() => { ga4.ctaClicked("whatsapp_asesoria"); ga4.whatsappOpened(); }}>
              <MessageCircle size={24} />
              <span style={{ fontWeight: 800 }}>Hablar con Taty</span>
              <span style={{ fontSize: "0.8125rem", opacity: 0.9, fontWeight: 500 }}>WhatsApp 24/7</span>
            </a>
            <a href={`/wizard/api/audit/pdf?email=${encodeURIComponent(store.paso1?.email || "")}&leadId=${encodeURIComponent(store.leadId || "")}`}
              target="_blank" className="ctx-btn-secondary"
              style={{ textDecoration: "none", textAlign: "center", padding: "1.25rem", borderRadius: "16px", display: "flex", flexDirection: "column", gap: "0.5rem", height: "auto", border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.05)" }}
              onClick={() => ga4.pdfDownloaded()}>
              <Download size={24} />
              <span style={{ fontWeight: 800 }}>Descargar PDF</span>
              <span style={{ fontSize: "0.8125rem", opacity: 0.9, fontWeight: 500 }}>Informe detallado</span>
            </a>
          </div>

          {/* Email CTA */}
          <div style={{ display: "flex", gap: "1rem", alignItems: "center", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "1.25rem", marginTop: "0.5rem" }}>
            <input
              type="email"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              placeholder="tu@email.com"
              className="ctx-input"
              style={{ flex: 1, margin: 0 }}
            />
            <button onClick={sendEmail} disabled={emailLoading || emailSent} className="ctx-btn-secondary"
              style={{ flexShrink: 0, padding: "0.75rem 1.5rem" }}>
              {emailSent ? "✅ Enviado" : emailLoading ? "..." : "Recibir por email"}
            </button>
          </div>
        </div>
      </div>
    </StepWrapper>
  );
}
