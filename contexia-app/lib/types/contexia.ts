/**
 * Tipos compartidos del dominio Contexia (mock-first).
 * Estos son los contratos que consumen pantallas y componentes.
 */

// === Primitivos ===
export type StatusLevel = "sana" | "vigilancia" | "alerta";
export type AlertSeverity = "warning" | "critical";
export type RiskLevel = "bajo" | "medio" | "alto";
export type ProgressVariant = "primary" | "success" | "warning" | "critical";
export type Scenario = "pesimista" | "base" | "optimista";
export type ProjectionTone = "warning" | "base" | "positive";

// === Pulso ===
export interface NoteOfDay {
  title: string;
  body: string;
}

export interface CashToday {
  total: number;
  yours: number;
  yesterdaySales: number;
  expenses: number;
  detailHref?: string;
}

export interface HealthKpi {
  id: "liquidez" | "rentabilidad" | "endeudamiento" | "eficiencia";
  icon: string; // Material Symbols name
  label: string;
  status: StatusLevel;
  detailHref?: string;
}

export interface ActiveAlert {
  id: string;
  icon: string; // Material Symbols name
  severity: AlertSeverity;
  message: string;
  href?: string;
}

export interface PulsoData {
  note: NoteOfDay;
  cash: CashToday;
  health: HealthKpi[];
  alerts: ActiveAlert[];
}

// === Fiscal (Centinela Fiscal) ===
export interface FiscalRiskStatus {
  level: RiskLevel;
  sectionLabel: string; // "Centinela Fiscal"
  levelLabel: string; // "Nivel de Riesgo: Bajo"
}

export interface ExAnteDetection {
  title: string;
  description: string;
  blockedCount: number;
}

export interface ShadowAuditMatch {
  title: string;
  highlight: string; // "100% de coincidencia"
  description: string;
}

export interface UvtThreshold {
  id: string;
  label: string;
  current: number;
  max: number;
  unit: string; // "UVT"
}

export interface TatyEscalation {
  title: string;
  subtitle: string;
  href?: string;
}

export interface FiscalData {
  risk: FiscalRiskStatus;
  exAnte: ExAnteDetection;
  shadowAudit: ShadowAuditMatch;
  thresholds: UvtThreshold[];
  taty: TatyEscalation;
}

// === Compartido ===

/** Segmento de texto rico, con highlights opcionales en color primary. */
export interface InsightSegment {
  text: string;
  highlight?: boolean;
}

/** Tarjeta de insight genérica usada en Radar, Patrimonio y FlujoDetalle. */
export interface Insight {
  body: InsightSegment[];
}

// === Radar (Radar Predictivo) ===

export interface CashProjection {
  /**
   * Tono visual del gráfico — controla stroke, gradiente del área,
   * glow e ícono del header. Se mapea a colores en el componente.
   */
  tone: ProjectionTone;
  /** Path SVG en viewBox 0..100 / 0..100. Y=0 es arriba, Y=100 es abajo. */
  pathD: string;
  /** Marcador vertical de obligación crítica (ej. IVA). */
  obligation: {
    label: string;
    /** Posición X en porcentaje (0-100) sobre el ancho del chart. */
    positionPct: number;
    /** Posición Y del punto sobre la línea (0=arriba, 100=abajo). */
    pointTopPct: number;
  };
  /** Etiquetas del eje X. */
  axisLabels: string[];
}

export interface TaxProvision {
  estimated: number;
  reserved: number;
  /** Porcentaje del avance hacia la meta (0-100). */
  goalPct: number;
}

export type StrategicInsight = Insight;

export interface UpcomingMilestone {
  id: string;
  monthAbbr: string; // "OCT", "NOV"
  day: string; // "15", "05"
  severity: AlertSeverity;
  title: string;
  subtitle: string;
  amount: number;
}

export interface RadarScenarioData {
  cashProjection: CashProjection;
  taxProvision: TaxProvision;
  strategicInsight: StrategicInsight;
  upcomingMilestones: UpcomingMilestone[];
}

export interface RadarData {
  header: {
    title: string;
    subtitle: string;
  };
  scenarios: Record<Scenario, RadarScenarioData>;
}

// === Patrimonio (Patrimonio & Escudo de Dividendos) ===

export interface PatrimonioTotal {
  total: number;
  retainedEarnings: number;
  currentYearEarnings: number;
}

export interface DividendShield {
  safeAmount: number; // Cantidad segura a retirar sin afectar operación
  safeZoneLabel: string; // "Zona Segura"
  riskLabel: string;
}

export interface WithdrawalScenario {
  amount: number; // Cantidad de retiro propuesta
  cashWithoutWithdrawal: number; // Caja sin retiro
  cashWithWithdrawal: number; // Caja con retiro calculada
  status: StatusLevel; // Estado derivado de ratio
  message: string; // Resumen del impacto
}

export interface EquityMovement {
  id: string;
  date: string; // "Octubre 2024"
  direction: "outflow" | "inflow"; // Para elegir ícono (south_east / north_east)
  label: string; // "Retiro de Socios" / "Aporte Extraordinario"
  amount: number;
}

export type StrategicPatrimonioInsight = Insight;

export interface PatrimonioData {
  header: {
    title: string;
    subtitle: string;
  };
  patrimonio: PatrimonioTotal;
  dividendShield: DividendShield;
  withdrawalSimulator: WithdrawalScenario;
  movements: EquityMovement[];
  insight: StrategicPatrimonioInsight;
}

// === Flujo Detalle (Salud Financiera Estructural) ===

export interface FlowCompositionItem {
  id: string;
  label: string; // "Operación", "Inversión", "Financiación"
  percentage: number; // 65, -15, 20
  color: string; // Tailwind class como "text-status-success"
}

export interface LiquidityBridge {
  initialBalance: number;
  inflows: number;
  outflows: number;
  finalBalance: number;
}

export interface FinancialHealthMetric {
  id: string;
  label: string; // "Liquidez", "Solvencia"
  description: string;
  status: StatusLevel; // "sana" o "vigilancia"
  percentage: number; // Para la barra de progreso
  color: string; // Tailwind class
}

export type StructuralFlowInsight = Insight;

export interface FlujoDetalleData {
  header: {
    title: string;
    subtitle: string;
  };
  insight: StructuralFlowInsight;
  flowComposition: FlowCompositionItem[];
  liquidityBridge: LiquidityBridge;
  healthMetrics: FinancialHealthMetric[];
}
