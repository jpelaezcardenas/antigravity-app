/**
 * Mock data + options for the Crear Empresa wizard
 */

import type { TipoSociedad } from "@/lib/types/crearEmpresa";

export interface TipoSociedadOption {
  id: TipoSociedad;
  label: string;
  subtitle: string;
  description: string;
  recommended?: boolean;
}

export const TIPOS_SOCIEDAD: TipoSociedadOption[] = [
  {
    id: "sas",
    label: "SAS",
    subtitle: "Sociedad por Acciones Simplificada",
    description:
      "La más común y flexible. Para 1 o más socios. Te protege a ti como persona — si algo pasa en la empresa, tu plata personal queda separada.",
    recommended: true,
  },
  {
    id: "sas-unipersonal",
    label: "SAS Unipersonal",
    subtitle: "SAS de una sola persona",
    description:
      "Si vas a arrancar tú solo, sin socios. Tiene la misma protección que la SAS clásica pero te ahorra trámites de socios.",
  },
  {
    id: "ltda",
    label: "Ltda",
    subtitle: "Sociedad Limitada",
    description:
      "Más tradicional. Requiere mínimo 2 socios. Menos flexible que la SAS — Taty solo la recomienda en casos específicos.",
  },
];

export const CIUDADES_COLOMBIA = [
  { value: "bogota", label: "Bogotá", departamento: "Cundinamarca" },
  { value: "medellin", label: "Medellín", departamento: "Antioquia" },
  { value: "cali", label: "Cali", departamento: "Valle del Cauca" },
  { value: "barranquilla", label: "Barranquilla", departamento: "Atlántico" },
  { value: "cartagena", label: "Cartagena", departamento: "Bolívar" },
  { value: "bucaramanga", label: "Bucaramanga", departamento: "Santander" },
  { value: "pereira", label: "Pereira", departamento: "Risaralda" },
  { value: "manizales", label: "Manizales", departamento: "Caldas" },
  { value: "cucuta", label: "Cúcuta", departamento: "Norte de Santander" },
  { value: "ibague", label: "Ibagué", departamento: "Tolima" },
  { value: "santa-marta", label: "Santa Marta", departamento: "Magdalena" },
  { value: "villavicencio", label: "Villavicencio", departamento: "Meta" },
];

export const CIIU_SUGERIDOS = [
  { code: "4711", label: "Comercio al por menor (tiendas, supermercados)" },
  { code: "6201", label: "Desarrollo de software, programación" },
  { code: "7020", label: "Consultoría empresarial y de gestión" },
  { code: "7320", label: "Publicidad y marketing digital" },
  { code: "9609", label: "Servicios personales (estética, fitness, etc.)" },
  { code: "5611", label: "Restaurantes" },
  { code: "4790", label: "Comercio al por menor online (e-commerce)" },
  { code: "8211", label: "Servicios administrativos" },
  { code: "4669", label: "Comercio al por mayor de otros productos" },
  { code: "8559", label: "Educación y capacitación" },
];

export interface PaymentMethodOption {
  id: string;
  label: string;
  subtitle: string;
  icon: string; // material symbol
  logos?: string[]; // optional brand logos to show
}

export const PAYMENT_METHODS: PaymentMethodOption[] = [
  {
    id: "transferencia",
    label: "Transferencia",
    subtitle: "Cuenta bancaria o billetera digital",
    icon: "account_balance",
    logos: ["Nequi", "Daviplata", "PSE"],
  },
  {
    id: "tarjeta",
    label: "Tarjeta débito o crédito",
    subtitle: "Visa, Mastercard, Amex",
    icon: "credit_card",
    logos: ["Visa", "Mastercard"],
  },
  {
    id: "bancolombia",
    label: "Corresponsales Bancolombia",
    subtitle: "Paga en punto físico",
    icon: "store",
  },
  {
    id: "pse",
    label: "PSE",
    subtitle: "Pago directo desde tu banco",
    icon: "language",
  },
];

/**
 * Mocked check: el nombre está "disponible" si tiene > 3 chars y no contiene
 * palabras prohibidas. Reemplazar en fase 2 con API real de Cámara de Comercio.
 */
export function checkNombreDisponibleMock(nombre: string): boolean {
  const trimmed = nombre.trim();
  if (trimmed.length < 4) return false;
  const prohibidas = ["banco", "estado", "republica", "nacional", "presidente"];
  const lower = trimmed.toLowerCase();
  return !prohibidas.some((p) => lower.includes(p));
}
