// ============================================================
// MOCK DATA — Contexia Frontend (Ferez.co E-commerce)
// Datos hardcodeados con hiperpersonalización para E-commerce
// ============================================================

// --- Usuario Mock ---
export const MOCK_USER = {
  usuario_id: 'usr_001',
  token: 'mock-jwt-token-contexia-2024',
  nombre_empresa: 'Ferez.co E-commerce',
  email: 'gerencia@ferez.co',
  nit: '901.456.789-2',
  plan: 'starter' as const,
  porcentaje_renta: 35,
  porcentaje_iva: 19,
  regimen: 'Régimen Ordinario',
};

// --- Pulso Diario ---
export const MOCK_PULSO = {
  usuario_id: 'usr_001',
  fecha: new Date().toISOString().split('T')[0],
  ingresos_brutos: 24_750_000,
  gastos_operativos: 14_230_000,
  margen_bruto: 10_520_000,
  porcentaje_tributario_estimado: 35,
  provision_dian: 3_682_000,
  dinero_tuyo_hoy: 6_838_000, // Libre de impuestos (Caja Real)
  ultima_sincronizacion: new Date().toISOString(),
  data_completa: true,
  advertencias: [] as string[],
  ventas_ayer: 3_340_000,
  gastos_ayer: 1_880_000,
  tendencia_30_dias: [
    { fecha: '01', valor: 3_200_000 },
    { fecha: '02', valor: 2_800_000 },
    { fecha: '03', valor: 4_100_000 },
    { fecha: '04', valor: 3_500_000 },
    { fecha: '05', valor: 3_900_000 },
    { fecha: '06', valor: 2_600_000 },
    { fecha: '07', valor: 4_500_000 },
    { fecha: '08', valor: 5_200_000 },
    { fecha: '09', valor: 4_800_000 },
    { fecha: '10', valor: 3_700_000 },
    { fecha: '11', valor: 4_200_000 },
    { fecha: '12', valor: 5_100_000 },
    { fecha: '13', valor: 4_600_000 },
    { fecha: '14', valor: 3_300_000 },
    { fecha: '15', valor: 5_800_000 },
    { fecha: '16', valor: 6_200_000 },
    { fecha: '17', valor: 5_500_000 },
    { fecha: '18', valor: 4_900_000 },
    { fecha: '19', valor: 5_300_000 },
    { fecha: '20', valor: 4_100_000 },
    { fecha: '21', valor: 3_800_000 },
    { fecha: '22', valor: 4_700_000 },
    { fecha: '23', valor: 5_600_000 },
    { fecha: '24', valor: 6_100_000 },
    { fecha: '25', valor: 5_000_000 },
    { fecha: '26', valor: 4_400_000 },
    { fecha: '27', valor: 5_900_000 },
    { fecha: '28', valor: 4_300_000 },
    { fecha: '29', valor: 5_200_000 },
    { fecha: '30', valor: 6_838_000 },
  ],
};

// --- Centinela Fiscal ---
export type Severidad = 'roja' | 'amarilla' | 'verde';

export interface AlertaTributaria {
  id: string;
  tipo: string;
  severidad: Severidad;
  titulo: string;
  descripcion: string;
  accion_sugerida: string;
  fecha_limite?: string;
  porcentaje_progreso?: number;
  umbral_nombre?: string;
}

export const MOCK_ALERTAS: AlertaTributaria[] = [
  {
    id: 'alerta_001',
    tipo: 'umbral',
    severidad: 'roja',
    titulo: '⚠️ Umbral de Declaración Superado',
    descripcion: 'Con las ventas de Shopify de esta semana cruzaste el límite (1,400 UVT). A partir de ahora declarar renta es obligatorio.',
    accion_sugerida: 'Tranquilo, tu Provisión DIAN ya está separando lo necesario de tus ventas diarias.',
    fecha_limite: '2026-08-12',
    porcentaje_progreso: 112,
    umbral_nombre: 'Renta Ordinaria (1,400 UVT)',
  },
  {
    id: 'alerta_002',
    tipo: 'vencimiento',
    severidad: 'roja',
    titulo: '📅 Alerta de IVA (Meta Ads / Proveedores)',
    descripcion: 'Faltan 5 días para tu declaración de IVA. Tu IVA descontable por pauta publicitaria ya fue calculado.',
    accion_sugerida: 'Asegúrate de subir cualquier factura de compra de inventario restante para reducir el pago.',
    fecha_limite: '2026-05-01',
  },
  {
    id: 'alerta_003',
    tipo: 'umbral',
    severidad: 'amarilla',
    titulo: '🔔 Responsabilidad de IVA a la vista',
    descripcion: 'El crecimiento de tu E-commerce es genial, pero te acercas al tope de 3,500 UVT para cobrar IVA en tus envíos.',
    accion_sugerida: 'Empieza a evaluar los márgenes de tus productos estrella si les sumas el 19%.',
    porcentaje_progreso: 85,
    umbral_nombre: 'Responsable IVA (3,500 UVT)',
  },
  {
    id: 'alerta_004',
    tipo: 'incumplimiento',
    severidad: 'verde',
    titulo: '✅ Blindaje Fiscal Activo',
    descripcion: 'Tus integraciones de pasarela (Stripe, Wompi) coinciden 100% con lo reportado a la DIAN este mes.',
    accion_sugerida: 'Ninguna acción requerida. Tienes claridad total sobre tu negocio.',
    fecha_limite: '2026-06-30',
  },
];

export const MOCK_CENTINELA = {
  usuario_id: 'usr_001',
  fecha_evaluacion: new Date().toISOString(),
  ingresos_acumulados_ytd: 98_200_000,
  alertas: MOCK_ALERTAS,
};

// --- Cobro Event-Driven ---
export interface FacturaVencida {
  id: string;
  numero_factura: string;
  cliente: string; // En E-commerce, usualmente es el proveedor logístico
  monto: number;
  fecha_emision: string;
  fecha_vencimiento: string;
  dias_vencida: number;
  estado: 'no_pagada' | 'parcialmente_pagada';
  intentos_cobro: number;
}

export const MOCK_CARTERA: FacturaVencida[] = [
  {
    id: 'fv_001',
    numero_factura: 'Recaudo PCE-0147',
    cliente: 'Inter Rapidísimo (Pago Contra Entrega)',
    monto: 4_850_000,
    fecha_emision: '2026-02-15',
    fecha_vencimiento: '2026-03-15',
    dias_vencida: 42,
    estado: 'no_pagada',
    intentos_cobro: 2,
  },
  {
    id: 'fv_002',
    numero_factura: 'Recaudo PCE-0152',
    cliente: 'Servientrega (Pago Contra Entrega)',
    monto: 12_300_000,
    fecha_emision: '2026-02-28',
    fecha_vencimiento: '2026-03-28',
    dias_vencida: 29,
    estado: 'no_pagada',
    intentos_cobro: 1,
  },
  {
    id: 'fv_003',
    numero_factura: 'Disp-Stripe-0158',
    cliente: 'Stripe Payouts',
    monto: 7_200_000,
    fecha_emision: '2026-03-01',
    fecha_vencimiento: '2026-03-05',
    dias_vencida: 26,
    estado: 'parcialmente_pagada',
    intentos_cobro: 1,
  },
  {
    id: 'fv_004',
    numero_factura: 'Recaudo PCE-0163',
    cliente: 'Envia (Pago Contra Entrega)',
    monto: 1_500_000,
    fecha_emision: '2026-01-20',
    fecha_vencimiento: '2026-02-20',
    dias_vencida: 65,
    estado: 'no_pagada',
    intentos_cobro: 4,
  },
];

// --- Taty (Chat Amiga Contadora) ---
export interface ChatMessage {
  id: string;
  role: 'user' | 'taty';
  content: string;
  timestamp: string;
}

export const MOCK_CHAT_INITIAL: ChatMessage[] = [
  {
    id: 'msg_001',
    role: 'taty',
    content: '¡Hola! 💚 Soy Taty, tu CFO as a Service. He analizado tus números de Ferez.co E-commerce de hoy. Tu caja real (lo que te queda después de provisión de impuestos) está genial. ¿Quieres revisar tus métricas de pauta o resolver una duda fiscal?',
    timestamp: new Date().toISOString(),
  },
];

export const TATY_RESPONSES: Record<string, string> = {
  'impuestos': '📊 ¡Súper! He revisado que tus ventas totales en Shopify y Wompi superan los $98M. No te preocupes por la declaración: tu provisión actual es de $3.6M y el sistema lo separa automáticamente de tu "Dinero tuyo hoy". ¿Quieres ver el detalle de deducciones?',
  'renta': '🏛️ Ya cruzaste el umbral de 1,400 UVT. En términos simples: sí debes declarar renta este año. Tu fecha límite es el 12 de agosto de 2026. Te enviaré recordatorios visuales (🟢🟡🔴) conforme nos acerquemos a la fecha para que estemos listos.',
  'deducciones': '💡 Para tu e-commerce, las deducciones de oro son:\n\n• Facturas de Meta Ads / Google Ads (Pauta)\n• Software como Shopify, Klaviyo\n• Costos de logística (Servientrega, Inter Rapidísimo)\n• Tu proveedor de pasarela (Wompi, Stripe)\n\n¿Estás solicitando factura electrónica a todos ellos?',
  'iva': '📋 Si llegas a las 3,500 UVT ($174M), serás responsable de IVA. Por ahora no lo eres, lo que te da una ventaja competitiva en el precio final de tus productos. Sigue monitoreando tu GPS Financiero.',
  'default': '¡Interesante! 🤔 Déjame revisar el impacto de eso en la caja real de Ferez.co. Te sugiero que agendemos una sesión rápida con uno de nuestros asesores expertos en E-commerce para revisarlo en detalle. ¿Te parece?',
};

export const TATY_SUGGESTIONS = [
  '¿Cuál es mi "Dinero tuyo hoy" libre de DIAN?',
  '¿Cuánto he gastado en pauta deducible?',
  '¿Qué facturas de transportadoras no he cruzado?',
  '¿Cuándo debo preocuparme por cobrar IVA?',
];

// --- Configuración ---
export const MOCK_CONFIG = {
  empresa: {
    nombre: 'Ferez.co E-commerce',
    nit: '901.456.789-2',
    plan: 'Starter',
    email: 'gerencia@ferez.co',
    telefono: '+57 312 456 7890',
    ciudad: 'Medellín',
  },
  tributario: {
    porcentaje_renta: 35,
    porcentaje_iva: 19,
    regimen: 'Régimen Ordinario',
    actividad_economica: '4791 - Comercio al por menor por internet',
    periodicidad_iva: 'Bimestral',
  },
  integraciones: [
    { nombre: 'Shopify', conectado: true, icono: '🛒' },
    { nombre: 'Stripe', conectado: true, icono: '💳' },
    { nombre: 'Wompi', conectado: true, icono: '💰' },
    { nombre: 'Siigo', conectado: true, icono: '📊' },
    { nombre: 'MercadoPago', conectado: false, icono: '🛍️' },
    { nombre: 'Nequi', conectado: false, icono: '📱' },
  ],
  notificaciones: {
    email: true,
    sms: false,
    push: true,
    alertas_criticas: true,
    resumen_semanal: true,
  },
};

// --- Formato Moneda COP ---
export const formatCOP = (value: number): string => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatCOPShort = (value: number): string => {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value}`;
};

