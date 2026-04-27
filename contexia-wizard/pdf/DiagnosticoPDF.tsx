import { Document, Page, Text, View, StyleSheet } from "@react-pdf/renderer";

// ─── Styles ──────────────────────────────────────────────────
const styles = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 10,
    color: "#1a202c",
    backgroundColor: "#ffffff",
    padding: 0,
  },
  header: {
    backgroundColor: "#0a2540",
    padding: "28 36",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontFamily: "Helvetica-Bold",
  },
  headerSubtitle: {
    color: "#94a3b8",
    fontSize: 10,
    marginTop: 4,
  },
  body: {
    padding: "24 36",
    flex: 1,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontFamily: "Helvetica-Bold",
    color: "#0a2540",
    marginBottom: 10,
    paddingBottom: 6,
    borderBottom: "1 solid #e2e8f0",
  },
  summaryCard: {
    backgroundColor: "#f0fdf4",
    border: "1.5 solid #86efac",
    borderRadius: 8,
    padding: "14 18",
    marginBottom: 16,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  summaryCardBlue: {
    backgroundColor: "#eff6ff",
    border: "1.5 solid #93c5fd",
  },
  regimenLabel: {
    fontSize: 15,
    fontFamily: "Helvetica-Bold",
    color: "#16a34a",
  },
  regimenLabelBlue: {
    color: "#2563eb",
  },
  ahorroBox: {
    backgroundColor: "#dcfce7",
    borderRadius: 6,
    padding: "8 12",
    alignItems: "center",
  },
  ahorroValue: {
    fontSize: 14,
    fontFamily: "Helvetica-Bold",
    color: "#16a34a",
  },
  ahorroLabel: {
    fontSize: 8,
    color: "#166534",
    marginTop: 2,
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 14,
  },
  metricCard: {
    flex: 1,
    backgroundColor: "#f8fafc",
    border: "1 solid #e2e8f0",
    borderRadius: 6,
    padding: "10 8",
    alignItems: "center",
  },
  metricValue: {
    fontSize: 13,
    fontFamily: "Helvetica-Bold",
    color: "#0a2540",
  },
  metricLabel: {
    fontSize: 8,
    color: "#64748b",
    marginTop: 3,
    textAlign: "center",
  },
  comparisonRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 10,
  },
  compCard: {
    flex: 1,
    border: "1 solid #e2e8f0",
    borderRadius: 8,
    padding: "12 14",
  },
  compCardActive: {
    border: "2 solid #00a878",
    backgroundColor: "#f0fdf4",
  },
  compCardActiveBlue: {
    border: "2 solid #2563eb",
    backgroundColor: "#eff6ff",
  },
  compCardTitle: {
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    color: "#0a2540",
    marginBottom: 6,
  },
  compValue: {
    fontSize: 16,
    fontFamily: "Helvetica-Bold",
    color: "#16a34a",
  },
  compValueBlue: {
    color: "#2563eb",
  },
  badge: {
    backgroundColor: "#00a878",
    borderRadius: 999,
    padding: "2 8",
    marginBottom: 6,
    alignSelf: "flex-start",
  },
  badgeText: {
    fontSize: 7,
    fontFamily: "Helvetica-Bold",
    color: "#ffffff",
  },
  riskCard: {
    borderRadius: 6,
    padding: "8 12",
    marginBottom: 6,
    flexDirection: "row",
    gap: 8,
    alignItems: "flex-start",
  },
  riskBadge: {
    borderRadius: 999,
    padding: "2 8",
    alignSelf: "flex-start",
    marginTop: 1,
  },
  riskTitle: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    color: "#0a2540",
    marginBottom: 3,
  },
  riskDesc: {
    fontSize: 9,
    color: "#475569",
    lineHeight: 1.5,
  },
  riskAction: {
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    color: "#0a2540",
    marginTop: 3,
  },
  planPhase: {
    marginBottom: 10,
  },
  planPhaseTitle: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    marginBottom: 5,
  },
  planItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 3,
  },
  planCheckbox: {
    width: 10,
    height: 10,
    border: "1 solid #cbd5e1",
    borderRadius: 2,
  },
  planItemText: {
    fontSize: 9,
    color: "#475569",
  },
  footer: {
    backgroundColor: "#f8fafc",
    borderTop: "1 solid #e2e8f0",
    padding: "14 36",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  footerText: {
    fontSize: 8,
    color: "#94a3b8",
  },
  disclaimer: {
    fontSize: 7.5,
    color: "#94a3b8",
    lineHeight: 1.6,
    marginTop: 4,
    borderTop: "1 solid #e2e8f0",
    paddingTop: 12,
  },
});

// ─── Helpers ──────────────────────────────────────────────────
function formatCOP(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(0)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function getRiesgoColor(nivel: string): { bg: string; textColor: string } {
  switch (nivel) {
    case "CRÍTICO": return { bg: "#fef2f2", textColor: "#dc2626" };
    case "ALTO": return { bg: "#fffbeb", textColor: "#d97706" };
    case "MEDIO": return { bg: "#eff6ff", textColor: "#2563eb" };
    default: return { bg: "#f0fdf4", textColor: "#16a34a" };
  }
}

// ─── PDF Document Component ───────────────────────────────────
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
  const esSimple = result.recomendacion === "simple";
  const fecha = new Date().toLocaleDateString("es-CO", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <Document title={`Shadow Audit — ${empresa}`} author="Contexia SAS">
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>Shadow Audit — Contexia</Text>
            <Text style={styles.headerSubtitle}>
              Diagnóstico tributario personalizado · {fecha}
            </Text>
          </View>
          <View style={{ alignItems: "flex-end" }}>
            <Text style={{ color: "#94a3b8", fontSize: 9 }}>Generado para</Text>
            <Text
              style={{
                color: "#ffffff",
                fontSize: 11,
                fontFamily: "Helvetica-Bold",
                marginTop: 2,
              }}
            >
              {nombre}
            </Text>
            <Text style={{ color: "#94a3b8", fontSize: 9, marginTop: 1 }}>
              {empresa}
            </Text>
          </View>
        </View>

        {/* Body */}
        <View style={styles.body}>
          {/* ── 1. Veredicto ── */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>1. Veredicto Tributario</Text>
            <View
              style={esSimple ? styles.summaryCard : [styles.summaryCard, styles.summaryCardBlue]}
            >
              <View>
                <Text
                  style={{ fontSize: 9, color: "#64748b", marginBottom: 4 }}
                >
                  RÉGIMEN RECOMENDADO
                </Text>
                <Text
                  style={esSimple ? styles.regimenLabel : [styles.regimenLabel, styles.regimenLabelBlue]}
                >
                  {esSimple ? "Régimen Simple" : "Régimen Ordinario"}
                </Text>
                <Text
                  style={{
                    fontSize: 11,
                    fontFamily: "Helvetica-Bold",
                    color: "#0a2540",
                    marginTop: 4,
                  }}
                >
                  {formatCOP(
                    esSimple ? result.impuestoSimple : result.impuestoOrdinario
                  )}
                  /año
                </Text>
              </View>
              {result.ahorroPotencial > 0 && (
                <View style={styles.ahorroBox}>
                  <Text style={styles.ahorroValue}>
                    💰 {formatCOP(result.ahorroPotencial)}
                  </Text>
                  <Text style={styles.ahorroLabel}>Ahorro potencial/año</Text>
                </View>
              )}
            </View>

            {/* Métricas */}
            <View style={styles.metricsRow}>
              {[
                {
                  label: "Ingresos anuales",
                  value: formatCOP(result.ingresosAnuales),
                  color: "#16a34a",
                },
                {
                  label: "Costos totales",
                  value: formatCOP(result.costosTotales),
                  color: "#dc2626",
                },
                {
                  label: "Utilidad bruta",
                  value: formatCOP(result.utilidadBruta),
                  color: "#2563eb",
                },
                {
                  label: "Margen neto",
                  value: `${result.margenPct?.toFixed(1) ?? 0}%`,
                  color: result.margenPct > 30 ? "#16a34a" : "#d97706",
                },
                {
                  label: "Readiness Score",
                  value: `${result.readinessScore}/100`,
                  color:
                    result.readinessBand === "verde"
                      ? "#16a34a"
                      : result.readinessBand === "ambar"
                      ? "#d97706"
                      : "#dc2626",
                },
              ].map((m) => (
                <View key={m.label} style={styles.metricCard}>
                  <Text style={[styles.metricValue, { color: m.color }]}>
                    {m.value}
                  </Text>
                  <Text style={styles.metricLabel}>{m.label}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* ── 2. Comparativo ── */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              2. Comparativo Simple vs Ordinario
            </Text>
            <View style={styles.comparisonRow}>
              <View
                style={esSimple ? styles.compCard : [styles.compCard, styles.compCardActive]}
              >
                {esSimple && (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>✅ RECOMENDADO</Text>
                  </View>
                )}
                <Text style={styles.compCardTitle}>Régimen Simple</Text>
                {result.impuestoSimple > 0 ? (
                  <>
                    <Text style={styles.compValue}>
                      {formatCOP(result.impuestoSimple)}/año
                    </Text>
                    <Text
                      style={{ fontSize: 8, color: "#64748b", marginTop: 4 }}
                    >
                      Renta + ICA integrados · IVA aparte
                    </Text>
                  </>
                ) : (
                  <Text style={{ fontSize: 9, color: "#dc2626" }}>
                    No aplica para tu nivel de ingresos
                  </Text>
                )}
              </View>
              <View
                style={!esSimple ? [styles.compCard, styles.compCardActiveBlue] : styles.compCard}
              >
                {!esSimple && (
                  <View style={[styles.badge, { backgroundColor: "#2563eb" }]}>
                    <Text style={styles.badgeText}>✅ RECOMENDADO</Text>
                  </View>
                )}
                <Text style={styles.compCardTitle}>Régimen Ordinario</Text>
                <Text style={[styles.compValue, styles.compValueBlue]}>
                  {formatCOP(result.impuestoOrdinario)}/año
                </Text>
                <Text style={{ fontSize: 8, color: "#64748b", marginTop: 4 }}>
                  Renta 35% + IVA neto + ICA municipal
                </Text>
              </View>
            </View>
          </View>

          {/* ── 3. Riesgos ── */}
          {result.riesgos?.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>
                3. Riesgos Identificados ({result.riesgos.length})
              </Text>
              {result.riesgos.slice(0, 6).map((r) => {
                const c = getRiesgoColor(r.nivel);
                return (
                  <View
                    key={r.titulo}
                    style={[styles.riskCard, { backgroundColor: c.bg }]}
                  >
                    <View
                      style={[
                        styles.riskBadge,
                        {
                          backgroundColor: c.bg,
                          border: `1 solid ${c.textColor}`,
                        },
                      ]}
                    >
                      <Text
                        style={{
                          fontSize: 7,
                          fontFamily: "Helvetica-Bold",
                          color: c.textColor,
                        }}
                      >
                        {r.nivel}
                      </Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.riskTitle}>{r.titulo}</Text>
                      <Text style={styles.riskDesc}>{r.descripcion}</Text>
                      <Text style={styles.riskAction}>✅ {r.accion}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {/* ── 4. Plan 30-60-90 ── */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              4. Plan de Acción 30-60-90 Días
            </Text>
            {[
              {
                label: "Días 0-30 — Constitución legal",
                color: "#2563eb",
                items: [
                  "Verificación de nombre en RUES",
                  "Redacción de estatutos SAS",
                  "Radicación en Cámara de Comercio",
                  "NIT + RUT con responsabilidades correctas",
                  "Habilitación facturación electrónica DIAN",
                ],
              },
              {
                label: "Días 30-60 — Cumplimiento sectorial",
                color: "#d97706",
                items: [
                  "Concepto de uso de suelos",
                  "Concepto sanitario municipal",
                  "Setup software contable",
                ],
              },
              {
                label: "Días 60-90 — Operación formalizada",
                color: "#16a34a",
                items: [
                  "Primera declaración Régimen Simple",
                  "Plan de contingencia regulatorio",
                  "Migración del establecimiento a nueva SAS",
                ],
              },
            ].map((fase) => (
              <View key={fase.label} style={styles.planPhase}>
                <Text
                  style={[styles.planPhaseTitle, { color: fase.color }]}
                >
                  {fase.label}
                </Text>
                {fase.items.map((item) => (
                  <View key={item} style={styles.planItem}>
                    <View style={styles.planCheckbox} />
                    <Text style={styles.planItemText}>{item}</Text>
                  </View>
                ))}
              </View>
            ))}
          </View>

          {/* Disclaimer */}
          <Text style={styles.disclaimer}>
            Disclaimer legal: Este diagnóstico es una herramienta de orientación
            generada automáticamente. NO constituye asesoría legal, contable o
            tributaria formal. Las cifras son estimaciones basadas en normativa
            vigente (E.T., Leyes 1943/2018, 2010/2019, 2155/2021, UVT 2026 =
            $49.799) y pueden variar al validar con sus números reales. La firma
            de declaraciones tributarias requiere Contador Público titulado.
          </Text>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            © 2026 Contexia SAS · growth@contexia.online · Medellín, Colombia
          </Text>
          <Text style={styles.footerText}>
            contexia.online · +57 301 894 8151
          </Text>
        </View>
      </Page>
    </Document>
  );
}
