"use client";

import type {
  AccionistaData,
  RepresentanteData,
  RepresentanteOrigen,
} from "@/lib/types/crearEmpresa";
import {
  formatCedula,
  formatTelefono,
} from "@/lib/utils/crearEmpresaLogic";
import { TatyTipCard } from "@/components/crear-empresa/TatyTipCard";

interface Step7RepresentanteProps {
  data: RepresentanteData;
  accionistas: AccionistaData[];
  onChange: (next: RepresentanteData) => void;
}

export function Step7Representante({
  data,
  accionistas,
  onChange,
}: Step7RepresentanteProps) {
  const setOrigen = (origen: RepresentanteOrigen) => {
    if (origen === "socio") {
      onChange({ origen, socioId: accionistas[0]?.id });
    } else {
      onChange({ origen, nombre: "", cedula: "", telefono: "", email: "" });
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2
          className="text-2xl md:text-3xl font-black text-white tracking-tight"
          style={{ fontFamily: "Rajdhani, sans-serif" }}
        >
          ¿Quién firma los papeles?
        </h2>
        <p className="text-on-surface-variant mt-1">
          Esta persona representa legalmente a la empresa: firma contratos, abre cuentas
          bancarias y toma decisiones oficiales.
        </p>
      </div>

      <TatyTipCard title="¿Qué hace el representante legal?" variant="violet">
        Es como el &quot;capitán&quot; de la empresa frente a otros: firma con bancos,
        proveedores, la DIAN, etc. Puede ser uno de los socios o alguien externo (un
        gerente). Lo puedes cambiar en cualquier momento.
      </TatyTipCard>

      <TatyTipCard title="✨ 100% digital — sin notaría">
        Buenas noticias: en Colombia ya puedes constituir tu SAS{" "}
        <strong className="text-[#2DD4BF]">totalmente online</strong> a través de la{" "}
        <strong className="text-white">Ventanilla Única Empresarial (VUE)</strong>.
        Todos los socios firman con <strong className="text-[#2DD4BF]">firma electrónica
        certificada</strong> (te la entrega la Cámara de Comercio). Ya no necesitas ir a
        notaría a autenticar nada. Si alguien no puede firmar digital, hacemos el trámite
        de autenticación presencial por ti.
      </TatyTipCard>

      {/* Toggle origen */}
      <div className="grid grid-cols-2 gap-2 p-1 bg-white/[0.03] border border-white/10 rounded-2xl">
        <button
          type="button"
          onClick={() => setOrigen("socio")}
          className={`py-3 rounded-xl text-sm font-bold transition-all ${
            data.origen === "socio"
              ? "bg-[#2DD4BF] text-[#020617] shadow-[0_0_16px_rgba(45,212,191,0.3)]"
              : "text-on-surface-variant hover:bg-white/[0.03]"
          }`}
        >
          Es un socio
        </button>
        <button
          type="button"
          onClick={() => setOrigen("otro")}
          className={`py-3 rounded-xl text-sm font-bold transition-all ${
            data.origen === "otro"
              ? "bg-[#2DD4BF] text-[#020617] shadow-[0_0_16px_rgba(45,212,191,0.3)]"
              : "text-on-surface-variant hover:bg-white/[0.03]"
          }`}
        >
          Otra persona
        </button>
      </div>

      {data.origen === "socio" ? (
        <div>
          <label
            className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            ¿Cuál socio?
          </label>
          {accionistas.length === 0 ? (
            <div className="bg-[#FACC15]/10 border border-[#FACC15]/30 rounded-xl px-4 py-3 text-sm text-[#FACC15]">
              Primero agrega socios en el paso anterior.
            </div>
          ) : (
            <select
              value={data.socioId || ""}
              onChange={(e) => onChange({ ...data, socioId: e.target.value })}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
            >
              <option value="">-- Selecciona --</option>
              {accionistas.map((a) => (
                <option key={a.id} value={a.id} className="bg-[#0F172A]">
                  {a.nombre || "(sin nombre)"} · {a.participacion}%
                </option>
              ))}
            </select>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label
                className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
                style={{ fontFamily: "Rajdhani, sans-serif" }}
              >
                Nombre completo
              </label>
              <input
                type="text"
                value={data.nombre || ""}
                onChange={(e) => onChange({ ...data, nombre: e.target.value })}
                placeholder="Nombre y apellido"
                className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
              />
            </div>
            <div>
              <label
                className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
                style={{ fontFamily: "Rajdhani, sans-serif" }}
              >
                Cédula
              </label>
              <input
                type="text"
                inputMode="numeric"
                value={data.cedula || ""}
                onChange={(e) => onChange({ ...data, cedula: formatCedula(e.target.value) })}
                placeholder="1.234.567.890"
                className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label
                className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
                style={{ fontFamily: "Rajdhani, sans-serif" }}
              >
                Teléfono
              </label>
              <input
                type="tel"
                inputMode="numeric"
                value={data.telefono || ""}
                onChange={(e) =>
                  onChange({ ...data, telefono: formatTelefono(e.target.value) })
                }
                placeholder="3001234567"
                className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
              />
            </div>
            <div>
              <label
                className="text-[11px] text-on-surface-variant font-bold uppercase tracking-widest block mb-2"
                style={{ fontFamily: "Rajdhani, sans-serif" }}
              >
                Correo
              </label>
              <input
                type="email"
                value={data.email || ""}
                onChange={(e) => onChange({ ...data, email: e.target.value })}
                placeholder="correo@ejemplo.com"
                className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-white placeholder-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]/50 focus:border-[#2DD4BF]/50 transition-all"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
