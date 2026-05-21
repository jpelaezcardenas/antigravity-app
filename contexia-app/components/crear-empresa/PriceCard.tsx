import { PRICE_CREAR_EMPRESA } from "@/lib/types/crearEmpresa";
import { formatCop } from "@/lib/format";

interface PriceCardProps {
  variant?: "full" | "compact";
}

const INCLUYE = [
  "Tu empresa lista en 5 días hábiles",
  "100% digital vía VUE (sin notaría)",
  "Firma electrónica certificada para todos los socios",
  "Registro en Cámara de Comercio (te ayudamos a hacerlo)",
  "Obtención del NIT ante la DIAN",
  "Certificado de existencia y representación legal",
  "Estatutos personalizados de tu empresa",
  "Asesoría legal y contable incluida",
  "Acompañamiento de Taty durante todo el proceso",
  "Shadow Audit gratis (valor $200K)",
  "1 mes de Contexia Pro incluido",
];

const NO_INCLUYE = [
  {
    label: "Cámara de Comercio",
    range: "$50.000 a $120.000",
    nota: "depende de tu capital — por eso lo dejamos bajo",
  },
  {
    label: "Firma electrónica (FEC)",
    range: "$60.000 aprox",
    nota: "una sola vez, queda guardada",
  },
];

export function PriceCard({ variant = "full" }: PriceCardProps) {
  if (variant === "compact") {
    return (
      <div className="bg-gradient-to-br from-[#2DD4BF]/10 to-[#8B5CF6]/5 border border-[#2DD4BF]/30 rounded-xl p-4 flex items-center justify-between gap-4 backdrop-blur-md">
        <div>
          <p
            className="text-[10px] text-[#2DD4BF] font-bold uppercase tracking-widest mb-1"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Crear tu empresa
          </p>
          <p
            className="text-2xl font-black text-white tracking-tight"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            {formatCop(PRICE_CREAR_EMPRESA)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-on-surface-variant">Pago único</p>
          <p className="text-[10px] text-[#2DD4BF] font-bold">Sin mensualidades</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#2DD4BF]/10 via-surface-elevated to-[#8B5CF6]/5 border border-[#2DD4BF]/30 rounded-2xl p-6 flex flex-col gap-4 backdrop-blur-md shadow-[0_0_30px_rgba(45,212,191,0.15)]">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <p
            className="text-[11px] text-[#2DD4BF] font-bold uppercase tracking-widest mb-1"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Crear tu empresa
          </p>
          <p
            className="text-4xl font-black text-white tracking-tight"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            {formatCop(PRICE_CREAR_EMPRESA)}
          </p>
          <p className="text-xs text-on-surface-variant mt-1">
            Pago único — Sin mensualidades
          </p>
        </div>
        <div className="text-right">
          <span className="inline-block px-3 py-1 bg-[#8B5CF6]/20 border border-[#8B5CF6]/40 rounded-full text-[10px] text-[#8B5CF6] font-bold uppercase tracking-widest">
            🔥 Lanzamiento
          </span>
        </div>
      </div>

      {/* Incluye */}
      <div className="flex flex-col gap-2 pt-3 border-t border-white/10">
        <p
          className="text-[11px] text-[#22C55E] font-bold uppercase tracking-widest"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Qué incluye
        </p>
        <ul className="flex flex-col gap-1.5">
          {INCLUYE.map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm text-on-surface">
              <span className="material-symbols-outlined text-[16px] text-[#22C55E] mt-0.5">
                check_circle
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* No incluye */}
      <div className="flex flex-col gap-2 pt-3 border-t border-white/10">
        <p
          className="text-[11px] text-[#FACC15] font-bold uppercase tracking-widest"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          Qué pagas aparte
        </p>
        <ul className="flex flex-col gap-2">
          {NO_INCLUYE.map((item) => (
            <li
              key={item.label}
              className="flex items-start gap-2 text-sm text-on-surface-variant"
            >
              <span className="material-symbols-outlined text-[16px] text-[#FACC15] mt-0.5">
                info
              </span>
              <span>
                <strong className="text-on-surface">{item.label}:</strong> {item.range}{" "}
                <em className="text-on-surface-variant/70">({item.nota})</em>
              </span>
            </li>
          ))}
        </ul>
        <p className="text-[11px] text-on-surface-variant/80 mt-1 italic">
          Te ayudamos a hacer esos pagos paso a paso — no hay sorpresas.
        </p>
      </div>
    </div>
  );
}
