// ============================================================
// MOCK DATA — Contexia Frontend
// Datos hardcodeados para demostración sin backend.
// Cuando el backend esté listo, reemplazar imports por API calls.
// ============================================================

// --- Usuario Mock ---
export const MOCK_USER = {
  usuario_id: 'usr_001',
  token: 'mock-jwt-token-contexia-2024',
  nombre_empresa: 'Ferez.co E-commerce',
  email: 'lavaderos_ld@contexia.com',
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
  ingresos_brutos: 18_750_000,
  gastos_operativos: 11_230_000,
  margen_bruto: 7_520_000,
  porcentaje_tributario_estimado: 35,
  provision_dian: 2_632_000,
  dinero_tuyo_hoy: 4_888_000,
  ultima_sincronizacion: new Date().toISOString(),
  data_completa: true,
  advertencias: [] as string[],
  ventas_ayer: 2_340_000,
  gastos_ayer: 1_180_000,
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
    { fecha: '30', valor: 4_888_000 },
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
    titulo: '⚠️ ¡Ya cruzaste el umbral de Renta Ordinaria!',
    descripcion: 'Tus ingresos acumulados este año superan 1,400 UVT ($69.7M COP). Ya eres declarante de renta obligatorio.',
    accion_sugerida: 'Agenda una cita con tu contador para preparar la declaración antes de la fecha límite.',
    fecha_limite: '2026-08-12',
    porcentaje_progreso: 112,
    umbral_nombre: 'Renta Ordinaria (1,400 UVT)',
  },
  {
    id: 'alerta_002',
    tipo: 'vencimiento',
    severidad: 'roja',
    titulo: '📅 Vencimiento IVA bimestral en 5 días',
    descripcion: 'El plazo para declarar y pagar IVA del bimestre actual vence el 1 de mayo. Monto estimado: $3,562,500 COP.',
    accion_sugerida: 'Revisa las facturas de compra pendientes para maximizar tu IVA descontable.',
    fecha_limite: '2026-05-01',
  },
  {
    id: 'alerta_003',
    tipo: 'umbral',
    severidad: 'amarilla',
    titulo: '🔔 Te acercas al umbral de Responsable de IVA',
    descripcion: 'Llevas $148.2M de $174.3M (3,500 UVT). Si cruzas este umbral, pasas a ser responsable de IVA.',
    accion_sugerida: 'Evalúa si te conviene frenar facturación este año o prepararte para el régimen de IVA.',
    porcentaje_progreso: 85,
    umbral_nombre: 'Responsable IVA (3,500 UVT)',
  },
  {
    id: 'alerta_004',
    tipo: 'incumplimiento',
    severidad: 'amarilla',
    titulo: '📋 Actualización RUT pendiente',
    descripcion: 'Tienes actividades económicas desactualizadas en tu RUT. La DIAN puede sancionarte.',
    accion_sugerida: 'Actualiza tu RUT en la página de la DIAN o con tu contador.',
    fecha_limite: '2026-06-30',
  },
  {
    id: 'alerta_005',
    tipo: 'umbral',
    severidad: 'verde',
    titulo: '✅ Retención en la fuente al día',
    descripcion: 'Tus pagos de retención en la fuente están al día. No hay pendientes.',
    accion_sugerida: 'Sigue así. La próxima declaración es en julio.',
    porcentaje_progreso: 45,
    umbral_nombre: 'Retención en la Fuente',
  },
];

export const MOCK_CENTINELA = {
  usuario_id: 'usr_001',
  fecha_evaluacion: new Date().toISOString(),
  ingresos_acumulados_ytd: 78_200_000,
  alertas: MOCK_ALERTAS,
};

// --- Cobro Event-Driven ---
export interface FacturaVencida {
  id: string;
  numero_factura: string;
  cliente: string;
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
    numero_factura: 'FV-2026-0147',
    cliente: 'Restaurante El Buen Sabor S.A.S',
    monto: 4_850_000,
    fecha_emision: '2026-02-15',
    fecha_vencimiento: '2026-03-15',
    dias_vencida: 42,
    estado: 'no_pagada',
    intentos_cobro: 2,
  },
  {
    id: 'fv_002',
    numero_factura: 'FV-2026-0152',
    cliente: 'Distribuidora Andina Ltda',
    monto: 12_300_000,
    fecha_emision: '2026-02-28',
    fecha_vencimiento: '2026-03-28',
    dias_vencida: 29,
    estado: 'no_pagada',
    intentos_cobro: 1,
  },
  {
    id: 'fv_003',
    numero_factura: 'FV-2026-0158',
    cliente: 'Hotel Parque Central',
    monto: 7_200_000,
    fecha_emision: '2026-03-01',
    fecha_vencimiento: '2026-03-31',
    dias_vencida: 26,
    estado: 'parcialmente_pagada',
    intentos_cobro: 1,
  },
  {
    id: 'fv_004',
    numero_factura: 'FV-2026-0163',
    cliente: 'Clínica Santa María',
    monto: 18_500_000,
    fecha_emision: '2026-01-20',
    fecha_vencimiento: '2026-02-20',
    dias_vencida: 65,
    estado: 'no_pagada',
    intentos_cobro: 4,
  },
  {
    id: 'fv_005',
    numero_factura: 'FV-2026-0170',
    cliente: 'Transportes del Valle S.A',
    monto: 3_150_000,
    fecha_emision: '2026-03-10',
    fecha_vencimiento: '2026-04-10',
    dias_vencida: 16,
    estado: 'no_pagada',
    intentos_cobro: 0,
  },
  {
    id: 'fv_006',
    numero_factura: 'FV-2026-0175',
    cliente: 'Constructora Medellín',
    monto: 25_800_000,
    fecha_emision: '2026-01-05',
    fecha_vencimiento: '2026-02-05',
    dias_vencida: 80,
    estado: 'no_pagada',
    intentos_cobro: 5,
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
    content: '¡Hola! 💚 Soy Taty, tu amiga contadora. Estoy aquí 24/7 para ayudarte con tus dudas de impuestos, flujo de caja y todo lo financiero. ¿En qué te puedo ayudar hoy?',
    timestamp: new Date().toISOString(),
  },
];

export const TATY_RESPONSES: Record<string, string> = {
  'impuestos': '📊 Basándome en tus ingresos acumulados de $78.2M COP este año, te recomiendo apartar aproximadamente $2.6M COP mensuales para impuestos. Así no te pilla la DIAN de sorpresa. ¿Quieres que te explique cómo calculé eso?',
  'renta': '🏛️ Para tu caso (Ferez.co E-commerce), como ya superaste los 1,400 UVT ($69.7M), eres declarante de renta obligatorio. La fecha límite según tu NIT es el 12 de agosto de 2026. ¡Tranqui, tenemos tiempo para preparar todo!',
  'deducciones': '💡 Para un negocio de lavandería como el tuyo, las principales deducciones son:\n\n• Arriendo del local\n• Servicios públicos (agua, luz)\n• Insumos de lavado\n• Nómina y prestaciones\n• Depreciación de máquinas\n• Mantenimiento de equipos\n\n¿Quieres que revisemos si tienes alguna que no estés aprovechando?',
  'iva': '📋 El IVA bimestral se declara cada 2 meses. Tu próximo vencimiento es el 1 de mayo. Recuerda que puedes descontar el IVA de las compras que hagas para tu negocio. Monto estimado a pagar: $3.5M COP.',
  'default': '¡Buena pregunta! 🤔 Déjame revisar... Para darte la mejor respuesta sobre tu caso específico con Ferez.co E-commerce, te sugiero que agendemos una sesión con uno de nuestros contadores expertos. ¿Te parece?',
};

export const TATY_SUGGESTIONS = [
  '¿Cuánto debo apartar para impuestos este mes?',
  '¿Cuándo debo declarar renta?',
  '¿Qué deducciones aplican a mi negocio?',
  '¿Cómo funciona el IVA bimestral?',
];

// --- Configuración ---
export const MOCK_CONFIG = {
  empresa: {
    nombre: 'Ferez.co E-commerce',
    nit: '901.456.789-2',
    plan: 'Starter',
    email: 'lavaderos_ld@contexia.com',
    telefono: '+57 312 456 7890',
    ciudad: 'Medellín',
  },
  tributario: {
    porcentaje_renta: 35,
    porcentaje_iva: 19,
    regimen: 'Régimen Ordinario',
    actividad_economica: '9601 - Lavado y limpieza de prendas de tela y de piel',
    periodicidad_iva: 'Bimestral',
  },
  integraciones: [
    { nombre: 'Siigo', conectado: true, icono: '📊' },
    { nombre: 'Bancolombia', conectado: true, icono: '🏦' },
    { nombre: 'Stripe', conectado: false, icono: '💳' },
    { nombre: 'Wompi', conectado: false, icono: '💰' },
    { nombre: 'MercadoPago', conectado: false, icono: '🛒' },
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
