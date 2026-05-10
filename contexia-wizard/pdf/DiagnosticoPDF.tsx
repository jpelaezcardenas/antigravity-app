import { Document, Page, Text, View, StyleSheet, Link } from "@react-pdf/renderer";

// ─── Color Palette ───────────────────────────────────────────
const C = {
  navy: "#0a2540",
  teal: "#2dd4bf",
  violet: "#7c3aed",
  white: "#ffffff",
  light: "#f8fafc",
  border: "#e2e8f0",
  muted: "#94a3b8",
  text: "#334155",
  green: "#16a34a",
  greenBg: "#f0fdf4",
  greenBorder: "#86efac",
  red: "#dc2626",
  redBg: "#fef2f2",
  orange: "#d97706",
  orangeBg: "#fffbeb",
  blue: "#2563eb",
  blueBg: "#eff6ff",
  blueBorder: "#93c5fd",
};

const s = StyleSheet.create({
  page: { fontFamily: "Helvetica", fontSize: 10, color: C.text, backgroundColor: C.white, padding: 0 },
  // Header
  header: { backgroundColor: C.navy, padding: "30 40", flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  headerBrand: { fontSize: 20, fontFamily: "Helvetica-Bold", color: C.white, letterSpacing: 1 },
  headerSub: { fontSize: 9, color: C.muted, marginTop: 4 },
  headerRight: { alignItems: "flex-end" },
  headerName: { color: C.white, fontSize: 12, fontFamily: "Helvetica-Bold", marginTop: 2 },
  headerCompany: { color: C.muted, fontSize: 9, marginTop: 2 },
  // Body
  body: { padding: "28 40", flex: 1 },
  section: { marginBottom: 22 },
  sectionTitle: { fontSize: 13, fontFamily: "Helvetica-Bold", color: C.navy, marginBottom: 10, paddingBottom: 6, borderBottom: `1.5 solid ${C.border}` },
  sectionNum: { color: C.teal, marginRight: 4 },
  // Veredicto
  verdictBox: { borderRadius: 10, padding: "16 20", marginBottom: 14, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  verdictLabel: { fontSize: 8, fontFamily: "Helvetica-Bold", color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 },
  verdictRegimen: { fontSize: 16, fontFamily: "Helvetica-Bold" },
  verdictTax: { fontSize: 12, fontFamily: "Helvetica-Bold", color: C.navy, marginTop: 4 },
  ahorroChip: { borderRadius: 8, padding: "10 14", alignItems: "center" },
  ahorroVal: { fontSize: 15, fontFamily: "Helvetica-Bold" },
  ahorroLbl: { fontSize: 7, marginTop: 2 },
  // Metrics
  metricsRow: { flexDirection: "row", gap: 10, marginBottom: 14 },
  metricCard: { flex: 1, backgroundColor: C.light, border: `1 solid ${C.border}`, borderRadius: 8, padding: "12 10", alignItems: "center" },
  metricVal: { fontSize: 14, fontFamily: "Helvetica-Bold" },
  metricLbl: { fontSize: 7.5, color: C.muted, marginTop: 4, textAlign: "center", textTransform: "uppercase", letterSpacing: 0.5 },
  // Comparison
  compRow: { flexDirection: "row", gap: 12, marginBottom: 10 },
  compCard: { flex: 1, border: `1 solid ${C.border}`, borderRadius: 10, padding: "14 16" },
  compActive: { border: `2 solid ${C.teal}`, backgroundColor: "#f0fdfa" },
  compActiveBlue: { border: `2 solid ${C.blue}`, backgroundColor: C.blueBg },
  compBadge: { backgroundColor: C.teal, borderRadius: 999, padding: "3 10", alignSelf: "flex-start", marginBottom: 8 },
  compBadgeBlue: { backgroundColor: C.blue },
  compBadgeText: { fontSize: 7, fontFamily: "Helvetica-Bold", color: C.white },
  compTitle: { fontSize: 11, fontFamily: "Helvetica-Bold", color: C.navy, marginBottom: 6 },
  compVal: { fontSize: 18, fontFamily: "Helvetica-Bold" },
  compNote: { fontSize: 8, color: C.muted, marginTop: 5 },
  // Risks
  riskCard: { borderRadius: 8, padding: "10 14", marginBottom: 8, flexDirection: "row", gap: 10, alignItems: "flex-start" },
  riskBadge: { borderRadius: 4, padding: "2 8", alignSelf: "flex-start", marginTop: 1 },
  riskTitle: { fontSize: 10, fontFamily: "Helvetica-Bold", color: C.navy, marginBottom: 3 },
  riskDesc: { fontSize: 9, color: C.text, lineHeight: 1.5 },
  riskAction: { fontSize: 9, fontFamily: "Helvetica-Bold", color: C.green, marginTop: 4 },
  // Plan
  planPhase: { marginBottom: 12 },
  planPhaseTitle: { fontSize: 10, fontFamily: "Helvetica-Bold", marginBottom: 6, paddingLeft: 8, borderLeft: "3 solid #e2e8f0" },
  planItem: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4, paddingLeft: 12 },
  planCheck: { width: 11, height: 11, border: `1.5 solid ${C.border}`, borderRadius: 3 },
  planText: { fontSize: 9, color: C.text, flex: 1 },
  // CTA
  ctaBox: { backgroundColor: C.navy, borderRadius: 12, padding: "24 28", marginTop: 6, marginBottom: 16, alignItems: "center" },
  ctaTitle: { fontSize: 15, fontFamily: "Helvetica-Bold", color: C.white, marginBottom: 6, textAlign: "center" },
  ctaSub: { fontSize: 10, color: C.muted, marginBottom: 16, textAlign: "center" },
  ctaRow: { flexDirection: "row", gap: 14 },
  ctaBtn: { borderRadius: 8, padding: "10 20", alignItems: "center" },
  ctaBtnPrimary: { backgroundColor: C.teal },
  ctaBtnSecondary: { backgroundColor: "rgba(255,255,255,0.1)", border: `1 solid rgba(255,255,255,0.2)` },
  ctaBtnText: { fontSize: 10, fontFamily: "Helvetica-Bold", color: C.navy },
  ctaBtnTextLight: { fontSize: 10, fontFamily: "Helvetica-Bold", color: C.white },
  ctaBtnSub: { fontSize: 7.5, color: C.muted, marginTop: 3 },
  // Footer
  footer: { backgroundColor: C.light, borderTop: `1 solid ${C.border}`, padding: "12 40", flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  footerText: { fontSize: 7.5, color: C.muted },
  disclaimer: { fontSize: 7, color: C.muted, lineHeight: 1.7, marginTop: 4, borderTop: `1 solid ${C.border}`, paddingTop: 12 },
});

// ─── Helpers ──────────────────────────────────────────────────
function fmt(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

function riskColor(nivel: string) {
  switch (nivel) {
    case "CRÍTICO": return { bg: C.redBg, tx: C.red };
    case "ALTO": return { bg: C.orangeBg, tx: C.orange };
    case "MEDIO": return { bg: C.blueBg, tx: C.blue };
    default: return { bg: C.greenBg, tx: C.green };
  }
}

// ─── Component ────────────────────────────────────────────────
interface Props {
  result: {
    recomendacion: "simple" | "ordinario";
    ingresosAnuales: number;
    costosTotales: number;
    utilidadBruta: number;
    margenPct: number;
    impuestoSimple: number;
    impuestoOrdinario: number;
    ahorroPotencial: number;
    readinessScore: number;
    readinessBand: "verde" | "ambar" | "rojo";
    riesgos: Array<{ nivel: string; titulo: string; descripcion: string; accion: string }>;
    oportunidades: Array<{ titulo: string; descripcion: string; impactoEstimado?: string }>;
  };
  nombre: string;
  empresa: string;
}

export function DiagnosticoPDF({ result, nombre, empresa }: Props) {
  const simple = result.recomendacion === "simple";
  const fecha = new Date().toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" });
  const scoreColor = result.readinessBand === "verde" ? C.green : result.readinessBand === "ambar" ? C.orange : C.red;

  return (
    <Document title={`Shadow Audit — ${empresa}`} author="Contexia SAS">
      <Page size="A4" style={s.page}>
        {/* ── Header ── */}
        <View style={s.header}>
          <View>
            <Text style={s.headerBrand}>CONTEXIA</Text>
            <Text style={s.headerSub}>Shadow Audit — Diagnostico tributario personalizado</Text>
            <Text style={s.headerSub}>{fecha}</Text>
          </View>
          <View style={s.headerRight}>
            <Text style={{ fontSize: 8, color: C.muted }}>PREPARADO PARA</Text>
            <Text style={s.headerName}>{nombre}</Text>
            <Text style={s.headerCompany}>{empresa}</Text>
          </View>
        </View>

        {/* ── Body ── */}
        <View style={s.body}>
          {/* 1. Veredicto */}
          <View style={s.section}>
            <Text style={s.sectionTitle}>1. Veredicto Tributario</Text>
            <View style={[s.verdictBox, { backgroundColor: simple ? "#f0fdfa" : C.blueBg, border: `1.5 solid ${simple ? C.teal : C.blueBorder}` }]}>
              <View>
                <Text style={s.verdictLabel}>Regimen recomendado</Text>
                <Text style={[s.verdictRegimen, { color: simple ? C.green : C.blue }]}>
                  {simple ? "Regimen Simple" : "Regimen Ordinario"}
                </Text>
                <Text style={s.verdictTax}>{fmt(simple ? result.impuestoSimple : result.impuestoOrdinario)}/año</Text>
              </View>
              {result.ahorroPotencial > 0 && (
                <View style={[s.ahorroChip, { backgroundColor: simple ? "#dcfce7" : "#dbeafe" }]}>
                  <Text style={[s.ahorroVal, { color: simple ? C.green : C.blue }]}>{fmt(result.ahorroPotencial)}</Text>
                  <Text style={[s.ahorroLbl, { color: simple ? "#166534" : "#1e40af" }]}>Ahorro potencial/año</Text>
                </View>
              )}
            </View>

            {/* Metrics */}
            <View style={s.metricsRow}>
              {[
                { l: "Ingresos anuales", v: fmt(result.ingresosAnuales), c: C.green },
                { l: "Costos totales", v: fmt(result.costosTotales), c: C.red },
                { l: "Utilidad bruta", v: fmt(result.utilidadBruta), c: C.blue },
                { l: "Margen neto", v: `${result.margenPct?.toFixed(1) ?? 0}%`, c: result.margenPct > 30 ? C.green : C.orange },
                { l: "Readiness", v: `${result.readinessScore}/100`, c: scoreColor },
              ].map((m) => (
                <View key={m.l} style={s.metricCard}>
                  <Text style={[s.metricVal, { color: m.c }]}>{m.v}</Text>
                  <Text style={s.metricLbl}>{m.l}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* 2. Comparativo */}
          <View style={s.section}>
            <Text style={s.sectionTitle}>2. Comparativo Simple vs Ordinario</Text>
            <View style={s.compRow}>
              {/* Simple */}
              <View style={[s.compCard, simple && s.compActive]}>
                {simple && <View style={s.compBadge}><Text style={s.compBadgeText}>RECOMENDADO</Text></View>}
                <Text style={s.compTitle}>Regimen Simple</Text>
                {result.impuestoSimple > 0 ? (
                  <>
                    <Text style={[s.compVal, { color: C.green }]}>{fmt(result.impuestoSimple)}/año</Text>
                    <Text style={s.compNote}>Renta + ICA integrados. IVA aparte si aplica.</Text>
                  </>
                ) : (
                  <Text style={{ fontSize: 9, color: C.red }}>No aplica para tu nivel de ingresos</Text>
                )}
              </View>
              {/* Ordinario */}
              <View style={[s.compCard, !simple && s.compActiveBlue]}>
                {!simple && <View style={[s.compBadge, s.compBadgeBlue]}><Text style={s.compBadgeText}>RECOMENDADO</Text></View>}
                <Text style={s.compTitle}>Regimen Ordinario</Text>
                <Text style={[s.compVal, { color: C.blue }]}>{fmt(result.impuestoOrdinario)}/año</Text>
                <Text style={s.compNote}>Renta 35% + IVA neto + ICA municipal</Text>
              </View>
            </View>
          </View>

          {/* 3. Riesgos */}
          {result.riesgos?.length > 0 && (
            <View style={s.section}>
              <Text style={s.sectionTitle}>3. Riesgos Identificados ({result.riesgos.length})</Text>
              {result.riesgos.slice(0, 5).map((r) => {
                const rc = riskColor(r.nivel);
                return (
                  <View key={r.titulo} style={[s.riskCard, { backgroundColor: rc.bg }]}>
                    <View style={[s.riskBadge, { backgroundColor: rc.bg, border: `1 solid ${rc.tx}` }]}>
                      <Text style={{ fontSize: 7, fontFamily: "Helvetica-Bold", color: rc.tx }}>{r.nivel}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={s.riskTitle}>{r.titulo}</Text>
                      <Text style={s.riskDesc}>{r.descripcion}</Text>
                      <Text style={s.riskAction}>→ {r.accion}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {/* 4. Plan 30-60-90 */}
          <View style={s.section}>
            <Text style={s.sectionTitle}>4. Plan de Accion 30-60-90 Dias</Text>
            {[
              { label: "Dias 0-30 — Constitucion legal", color: C.violet, items: ["Verificacion de nombre en RUES", "Redaccion de estatutos SAS", "Radicacion en Camara de Comercio", "NIT + RUT con responsabilidades correctas", "Habilitacion facturacion electronica DIAN", "Apertura cuenta bancaria empresarial"] },
              { label: "Dias 30-60 — Cumplimiento sectorial", color: C.orange, items: ["Concepto de uso de suelos", "Concepto sanitario municipal", "Setup software contable (Siigo / Alegra)"] },
              { label: "Dias 60-90 — Operacion formalizada", color: C.green, items: ["Primera declaracion Regimen Simple", "Plan de contingencia regulatorio", "Migracion del establecimiento a nueva SAS"] },
            ].map((fase) => (
              <View key={fase.label} style={s.planPhase}>
                <Text style={[s.planPhaseTitle, { color: fase.color, borderLeftColor: fase.color }]}>{fase.label}</Text>
                {fase.items.map((item) => (
                  <View key={item} style={s.planItem}>
                    <View style={[s.planCheck, { borderColor: fase.color }]} />
                    <Text style={s.planText}>{item}</Text>
                  </View>
                ))}
              </View>
            ))}
          </View>

          {/* 5. CTA */}
          <View style={s.ctaBox}>
            <Text style={s.ctaTitle}>¿Listo para formalizar tu empresa?</Text>
            <Text style={s.ctaSub}>Contexia te acompaña en cada paso. Desde la constitucion SAS hasta tu primera declaracion.</Text>
            <View style={s.ctaRow}>
              <Link src="https://www.contexia.online/crear-empresa.html" style={{ textDecoration: "none" }}>
                <View style={[s.ctaBtn, s.ctaBtnPrimary]}>
                  <Text style={s.ctaBtnText}>Crear mi empresa</Text>
                  <Text style={[s.ctaBtnSub, { color: "#065f46" }]}>Paquetes desde $1.2M</Text>
                </View>
              </Link>
              <Link src="https://cal.com/juan-david-pelaez-cardenas-jrurh5/30min" style={{ textDecoration: "none" }}>
                <View style={[s.ctaBtn, s.ctaBtnSecondary]}>
                  <Text style={s.ctaBtnTextLight}>Agendar asesoria</Text>
                  <Text style={s.ctaBtnSub}>30 min gratis</Text>
                </View>
              </Link>
              <Link src="https://www.contexia.online" style={{ textDecoration: "none" }}>
                <View style={[s.ctaBtn, s.ctaBtnSecondary]}>
                  <Text style={s.ctaBtnTextLight}>contexia.online</Text>
                  <Text style={s.ctaBtnSub}>Ver servicios</Text>
                </View>
              </Link>
            </View>
          </View>

          {/* Disclaimer */}
          <Text style={s.disclaimer}>
            Disclaimer legal: Este diagnostico es una herramienta de orientacion generada automaticamente. NO constituye asesoria legal, contable o tributaria formal. Las cifras son estimaciones basadas en normativa vigente (E.T., Leyes 1943/2018, 2010/2019, 2155/2021, UVT 2026 = $49.799) y pueden variar al validar con sus numeros reales. La firma de declaraciones tributarias requiere Contador Publico titulado.
          </Text>
        </View>

        {/* ── Footer ── */}
        <View style={s.footer}>
          <Text style={s.footerText}>© 2026 Contexia SAS · NIT en tramite · Medellin, Colombia</Text>
          <Text style={s.footerText}>growth@contexia.online · +57 301 894 8151 · contexia.online</Text>
        </View>
      </Page>
    </Document>
  );
}
