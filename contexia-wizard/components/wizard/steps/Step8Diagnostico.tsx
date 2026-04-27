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
      background: "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
      borderRadius: "12px",
      padding: "1.25rem 1.5rem",
      marginBottom: "1.5rem",
      display: "flex",
      gap: "1rem",
      alignItems: "flex-start",
    }}>
      <span style={{ fontSize: "1.5rem", flexShrink: 0 }}>⚡</span>
      <div>
        <h4 style={{ color: "#ffffff", fontWeight: 700, fontSize: "0.9375rem", margin: "0 0 0.375rem" }}>
          Atención CIIU 1090 — Elaboración de otros productos alimenticios
        </h4>
        <p style={{ color: "#c4b5fd", fontSize: "0.8125rem", margin: "0 0 0.75rem", lineHeight: 1.6 }}>
          Tu actividad está sujeta a regulación del INVIMA y BPM (Buenas Prácticas de Manufactura).
          Antes de formalizar, verifica el certificado sanitario y el concepto de uso de suelos.
        </p>
        <a
          href="https://wa.me/573018948151?text=Hola%20Taty,%20tengo%20CIIU%201090%20y%20necesito%20orientación%20sobre%20INVIMA%20y%20BPM"
          target="_blank" rel="noopener noreferrer"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.375rem",
            background: "rgba(255,255,255,0.15)",
            border: "1px solid rgba(255,255,255,0.3)",
            color: "#ffffff",
            fontSize: "0.8125rem",
            fontWeight: 600,
            padding: "0.5rem 1rem",
            borderRadius: "8px",
            textDecoration: "none",
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
        <path d="M 10 90 A 80 80 0 0 1 170 90" fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round" />
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
        <text x="90" y="80" textAnchor="middle" fontSize="28" fontWeight="700" fill={color}>{score}</text>
        <text x="90" y="96" textAnchor="middle" fontSize="11" fill="#94a3b8">/100</text>
      </svg>
    </div>
  );
}

function RiesgoCard({ riesgo }: { riesgo: any }) {
  const config: Record<string, { bg: string; border: string; color: string; icon: any; label: string }> = {
    CRÍTICO: { bg: "#fef2f2", border: "#fca5a5", color: "#dc2626", icon: XCircle, label: "CRÍTICO" },
    ALTO: { bg: "#fffbeb", border: "#fcd34d", color: "#d97706", icon: AlertTriangle, label: "ALTO" },
    MEDIO: { bg: "#eff6ff", border: "#93c5fd", color: "#2563eb", icon: AlertTriangle, label: "MEDIO" },
    BAJO: { bg: "#f0fdf4", border: "#86efac", color: "#16a34a", icon: CheckCircle, label: "BAJO" },
  };
  const c = config[riesgo.nivel] || config.MEDIO;
  const Icon = c.icon;

  return (
    <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: "10px", padding: "1rem 1.25rem" }}>
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
        <Icon size={18} color={c.color} style={{ flexShrink: 0, marginTop: "2px" }} />
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.375rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: c.color, background: "rgba(255,255,255,0.7)", padding: "0.125rem 0.5rem", borderRadius: "999px", border: `1px solid ${c.border}` }}>{c.label}</span>
            <h4 style={{ color: "#0a2540", fontWeight: 700, fontSize: "0.9375rem", margin: 0 }}>{riesgo.titulo}</h4>
          </div>
          <p style={{ color: "#475569", fontSize: "0.875rem", margin: "0 0 0.5rem", lineHeight: 1.6 }}>{riesgo.descripcion}</p>
          <p style={{ color: "#0a2540", fontSize: "0.875rem", fontWeight: 600, margin: 0 }}>✅ {riesgo.accion}</p>
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

  return (
    <StepWrapper
      step={8}
      headline="Tu diagnóstico Contexia"
      subheadline="Análisis tributario personalizado basado en tu información."
      onBack={onBack}
      isLastStep
    >
      {!auditDone ? (
        /* ── Pre-audit CTA ── */
        <div style={{ textAlign: "center", padding: "3rem 1rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
          <h3 style={{ fontSize: "1.375rem", fontWeight: 700, color: "#0a2540", marginBottom: "0.75rem" }}>
            Todo listo para tu Shadow Audit
          </h3>
          <p style={{ color: "#64748b", fontSize: "0.9375rem", maxWidth: "480px", margin: "0 auto 2rem" }}>
            Analizaremos tu caso en segundos: Simple vs Ordinario, riesgos DIAN, oportunidades y tu plan de acción.
          </p>
          <button onClick={executeAudit} disabled={loading} className="ctx-btn-primary"
            style={{ fontSize: "1rem", padding: "0.875rem 2.5rem", borderRadius: "12px" }}>
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span className="animate-spin" style={{ display: "inline-block", width: "18px", height: "18px", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%" }} />
                Ejecutando análisis...
              </span>
            ) : "🔍 Ejecutar Shadow Audit"}
          </button>
          {loading && (
            <div style={{ marginTop: "1.5rem", color: "#94a3b8", fontSize: "0.875rem" }}>
              <p>Calculando regímenes tributarios...</p>
              <p>Identificando riesgos DIAN...</p>
              <p>Proyectando ahorros...</p>
            </div>
          )}
        </div>
      ) : result ? (
        /* ── Full diagnostic ── */
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* CIIU 1090 special banner */}
          {store.paso2?.ciiu_principal === "1090" && <Ciiu1090Banner />}
          {/* A — Resumen ejecutivo */}
          <div style={{
            background: result.recomendacion === "simple" ? "#f0fdf4" : "#eff6ff",
            border: `1px solid ${result.recomendacion === "simple" ? "#86efac" : "#93c5fd"}`,
            borderRadius: "14px", padding: "1.5rem",
          }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <h3 style={{ fontWeight: 700, fontSize: "1.125rem", color: "#0a2540", margin: "0 0 0.25rem" }}>
                  {store.paso2?.nombre_opcion1 || "Tu empresa"}
                </h3>
                <p style={{ color: "#475569", fontSize: "0.875rem", margin: 0 }}>
                  Régimen recomendado:{" "}
                  <strong style={{ color: result.recomendacion === "simple" ? "#16a34a" : "#2563eb" }}>
                    {result.recomendacion === "simple" ? "Régimen Simple" : "Régimen Ordinario"}
                  </strong>
                </p>
              </div>
              <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.375rem", fontWeight: 700, color: "#16a34a" }}>{formatMillones(result.ahorroPotencial)}</div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Ahorro potencial/año</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.375rem", fontWeight: 700, color: result.readinessBand === "verde" ? "#16a34a" : result.readinessBand === "ambar" ? "#d97706" : "#dc2626" }}>
                    {result.readinessScore}/100
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Readiness Score</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.375rem", fontWeight: 700, color: "#dc2626" }}>{result.riesgos.length}</div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Riesgos críticos/altos</div>
                </div>
              </div>
            </div>
          </div>

          {/* B — Proyección financiera */}
          <div className="ctx-card">
            <h3 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <TrendingUp size={18} /> Proyección Financiera Anual
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
              {[
                { label: "Ingresos anuales", val: formatMillones(result.ingresosAnuales), color: "#16a34a" },
                { label: "Costos totales", val: formatMillones(result.costosTotales), color: "#dc2626" },
                { label: "Utilidad bruta", val: formatMillones(result.utilidadBruta), color: "#2563eb" },
                { label: "Margen neto", val: `${result.margenPct.toFixed(1)}%`, color: result.margenPct > 30 ? "#16a34a" : "#d97706" },
              ].map((item) => (
                <div key={item.label} style={{ background: "#f8fafc", borderRadius: "10px", padding: "1rem", textAlign: "center" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: item.color }}>{item.val}</div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.25rem" }}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* C — Comparativo Simple vs Ordinario */}
          <div>
            <h3 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "1rem" }}>Comparativo: Simple vs Ordinario</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              {/* Simple */}
              <div style={{
                border: `2px solid ${result.recomendacion === "simple" ? "#00a878" : "#e2e8f0"}`,
                borderRadius: "12px", padding: "1.25rem",
                background: result.recomendacion === "simple" ? "#f0fdf4" : "#fff",
              }}>
                {result.recomendacion === "simple" && (
                  <div style={{ background: "#00a878", color: "#fff", fontSize: "0.75rem", fontWeight: 700, padding: "0.25rem 0.75rem", borderRadius: "999px", display: "inline-flex", marginBottom: "0.75rem" }}>
                    ✅ RECOMENDADO
                  </div>
                )}
                <h4 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "0.75rem" }}>Régimen Simple</h4>
                {result.impuestoSimple > 0 ? (
                  <>
                    <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>{formatMillones(result.impuestoSimple)}/año</div>
                    <div style={{ fontSize: "0.8125rem", color: "#64748b", marginTop: "0.5rem" }}>
                      Incluye: Renta + ICA integrados · IVA aparte si aplica
                    </div>
                  </>
                ) : (
                  <p style={{ color: "#dc2626", fontSize: "0.875rem" }}>❌ No aplica para tu nivel de ingresos</p>
                )}
              </div>
              {/* Ordinario */}
              <div style={{
                border: `2px solid ${result.recomendacion === "ordinario" ? "#2563eb" : "#e2e8f0"}`,
                borderRadius: "12px", padding: "1.25rem",
                background: result.recomendacion === "ordinario" ? "#eff6ff" : "#fff",
              }}>
                {result.recomendacion === "ordinario" && (
                  <div style={{ background: "#2563eb", color: "#fff", fontSize: "0.75rem", fontWeight: 700, padding: "0.25rem 0.75rem", borderRadius: "999px", display: "inline-flex", marginBottom: "0.75rem" }}>
                    ✅ RECOMENDADO
                  </div>
                )}
                <h4 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "0.75rem" }}>Régimen Ordinario</h4>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{formatMillones(result.impuestoOrdinario)}/año</div>
                <div style={{ fontSize: "0.8125rem", color: "#64748b", marginTop: "0.5rem" }}>
                  Renta 35% + IVA neto + ICA municipal
                </div>
              </div>
            </div>
            {result.ahorroPotencial > 0 && (
              <div style={{ marginTop: "0.75rem", background: "#f0fdf4", border: "1px solid #86efac", borderRadius: "10px", padding: "0.875rem 1.25rem", display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span style={{ fontSize: "1.25rem" }}>💰</span>
                <span style={{ fontWeight: 700, color: "#16a34a" }}>
                  Veredicto: Ahorras {formatMillones(result.ahorroPotencial)}/año eligiendo el régimen correcto
                </span>
              </div>
            )}
          </div>

          {/* D — Riesgos */}
          {result.riesgos.length > 0 && (
            <div>
              <h3 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "1rem" }}>
                ⚠️ Riesgos Identificados ({result.riesgos.length})
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {result.riesgos.map((r) => <RiesgoCard key={r.titulo} riesgo={r} />)}
              </div>
            </div>
          )}

          {/* E — Oportunidades */}
          {result.oportunidades.length > 0 && (
            <div>
              <h3 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "1rem" }}>💡 Oportunidades</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {result.oportunidades.map((o) => (
                  <div key={o.titulo} style={{ background: "#f0fdf4", border: "1px solid #86efac", borderRadius: "10px", padding: "1rem 1.25rem" }}>
                    <h4 style={{ color: "#16a34a", fontWeight: 700, margin: "0 0 0.375rem", fontSize: "0.9375rem" }}>{o.titulo}</h4>
                    <p style={{ color: "#475569", fontSize: "0.875rem", margin: 0 }}>{o.descripcion}</p>
                    {o.impactoEstimado && <p style={{ color: "#16a34a", fontSize: "0.875rem", fontWeight: 600, marginTop: "0.375rem" }}>{o.impactoEstimado}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* F — Plan 30-60-90 */}
          <div>
            <h3 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "1rem" }}>📅 Plan de Acción 30-60-90 Días</h3>
            {[
              { label: "Días 0-30 — Constitución legal", color: "#2563eb", items: ["Verificación de nombre en RUES", "Redacción de estatutos SAS", "Radicación en Cámara de Comercio", "NIT + RUT con responsabilidades correctas", "Habilitación facturación electrónica DIAN", "Apertura cuenta bancaria empresarial"] },
              { label: "Días 30-60 — Cumplimiento sectorial", color: "#d97706", items: ["Concepto de uso de suelos", "Concepto sanitario municipal", "Inicio trámite registro ICA en SimplifICA (si aplica)", "Setup software contable (Siigo / Alegra)"] },
              { label: "Días 60-90 — Operación formalizada", color: "#16a34a", items: ["Migración del establecimiento existente a la nueva SAS", "Primera declaración Régimen Simple", "Plan de contingencia regulatorio", "Capacitación BPMAA (si aplica)"] },
            ].map((fase) => (
              <div key={fase.label} style={{ marginBottom: "1rem" }}>
                <h4 style={{ fontWeight: 700, color: fase.color, fontSize: "0.9375rem", marginBottom: "0.625rem" }}>{fase.label}</h4>
                <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {fase.items.map((item) => (
                    <li key={item} style={{ display: "flex", alignItems: "center", gap: "0.625rem", fontSize: "0.875rem", color: "#475569" }}>
                      <span style={{ width: "18px", height: "18px", border: "2px solid #e2e8f0", borderRadius: "4px", flexShrink: 0, display: "inline-block" }} />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* G — Readiness Score */}
          <div className="ctx-card" style={{ textAlign: "center" }}>
            <h3 style={{ fontWeight: 700, color: "#0a2540", marginBottom: "0.5rem" }}>Readiness Score</h3>
            <ReadinessGauge score={result.readinessScore} band={result.readinessBand} />
            <p style={{ fontWeight: 700, color: result.readinessBand === "verde" ? "#16a34a" : result.readinessBand === "ambar" ? "#d97706" : "#dc2626", marginTop: "0.5rem" }}>
              {result.readinessScore >= 80 ? "Listo para formalizar — Empieza ya" : result.readinessScore >= 50 ? "Requiere ajustes — Te acompañamos" : "Foundation building crítico — Paquete completo recomendado"}
            </p>
          </div>

          {/* Disclaimer */}
          <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "1rem 1.25rem" }}>
            <p style={{ fontSize: "0.8125rem", color: "#94a3b8", margin: 0, lineHeight: 1.7 }}>
              <strong>Disclaimer legal:</strong> Este diagnóstico es una herramienta de orientación generada automáticamente. NO constituye asesoría legal, contable o tributaria formal. Las cifras son estimaciones basadas en normativa vigente (E.T., Leyes 1943/2018, 2010/2019, 2155/2021) y pueden variar al validar con tus números reales. La firma de declaraciones tributarias requiere Contador Público titulado.
            </p>
          </div>

          {/* H — CTAs */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h3 style={{ fontWeight: 700, color: "#0a2540", margin: "0 0 0.5rem" }}>¿Qué sigue?</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
              <a href="https://www.contexia.online/crear-empresa.html" className="ctx-btn-primary"
                style={{ textDecoration: "none", textAlign: "center", padding: "0.875rem", borderRadius: "12px", flexDirection: "column", gap: "0.25rem" }}
                onClick={() => ga4.ctaClicked("crear_empresa")}>
                <Building2 size={20} />
                <span>Crear mi empresa con Contexia</span>
                <span style={{ fontSize: "0.8125rem", opacity: 0.85 }}>Desde $1.200.000 COP</span>
              </a>
              <a href="https://wa.me/573018948151?text=Hola,%20completé%20el%20Shadow%20Audit%20y%20quiero%20agendar%20asesoría"
                target="_blank" rel="noopener noreferrer" className="ctx-btn-secondary"
                style={{ textDecoration: "none", textAlign: "center", padding: "0.875rem", borderRadius: "12px", flexDirection: "column", gap: "0.25rem" }}
                onClick={() => { ga4.ctaClicked("whatsapp_asesoria"); ga4.whatsappOpened(); }}>
                <MessageCircle size={20} />
                <span>Hablar con Taty</span>
                <span style={{ fontSize: "0.8125rem", opacity: 0.85 }}>WhatsApp 24/7</span>
              </a>
              <a href={`/wizard/api/audit/pdf?email=${encodeURIComponent(store.paso1?.email || "")}&leadId=${encodeURIComponent(store.leadId || "")}`}
                target="_blank" className="ctx-btn-outline"
                style={{ textDecoration: "none", textAlign: "center", padding: "0.875rem", borderRadius: "12px", flexDirection: "column", gap: "0.25rem", display: "flex", alignItems: "center", justifyContent: "center" }}
                onClick={() => ga4.pdfDownloaded()}>
                <Download size={20} />
                <span>Descargar PDF</span>
              </a>
            </div>

            {/* Email CTA */}
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "1rem" }}>
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="tu@email.com"
                className="ctx-input"
                style={{ flex: 1 }}
              />
              <button onClick={sendEmail} disabled={emailLoading || emailSent} className="ctx-btn-secondary"
                style={{ flexShrink: 0 }}>
                {emailSent ? "✅ Enviado" : emailLoading ? "Enviando..." : "Recibir por email"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </StepWrapper>
  );
}
