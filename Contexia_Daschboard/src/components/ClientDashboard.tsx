import React from 'react';

export const ClientDashboard = ({ setActiveTab, clienteNombre }: { setActiveTab: (t: string) => void, clienteNombre: string }) => {
  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-4xl mx-auto px-4 lg:px-8 mt-6">
      {/* Taty Note of the Day Banner */}
      <section className="bg-gradient-to-r from-ctx-teal/20 to-transparent border-l-4 border-ctx-teal rounded-r-xl p-4 md:p-6 mb-2">
        <div className="flex gap-4">
          <div className="w-10 h-10 rounded-full bg-ctx-teal/20 flex items-center justify-center flex-shrink-0 mt-1">
            <span className="material-symbols-outlined text-ctx-teal" style={{ fontVariationSettings: "'FILL' 1" }}>
              smart_toy
            </span>
          </div>
          <div>
            <h2 className="font-title-md text-title-md text-white mb-1">
              Hoy en tu negocio
            </h2>
            <p className="font-body-md text-body-md text-on-surface leading-relaxed">
              Tu plata está sana, pero bajó un poco por una cuota del banco. Nada grave, sigue tranqui.
            </p>
          </div>
        </div>
      </section>

      {/* Cash Today Card */}
      <section className="bg-[#111827] rounded-xl p-6 border border-white/10 shadow-[0_0_20px_rgba(45,212,191,0.05)] relative overflow-hidden">
        <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-emerald-500/10 to-transparent pointer-events-none" />
        <div className="relative z-10">
          <h2 className="text-gray-400 text-sm mb-2 font-rajdhani uppercase tracking-widest">
            Caja Real de Hoy
          </h2>
          <div className="text-4xl md:text-5xl font-orbitron font-bold text-emerald-400 mb-2 tracking-tight">
            $42.850.000
          </div>
          <p className="text-white text-lg font-bold mb-6">
            Dinero tuyo de verdad: <span className="text-emerald-300">$38.500.000</span>
          </p>

          <div className="flex flex-col gap-3 border-t border-white/10 pt-5">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 font-mono text-sm">Ventas de ayer:</span>
              <span className="text-white font-mono text-sm">$1.250.000</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 font-mono text-sm">Salidas de plata:</span>
              <span className="text-white font-mono text-sm">$345.000</span>
            </div>
          </div>

          <button
            onClick={() => setActiveTab('flujo-detalle')}
            className="mt-6 w-full flex items-center justify-center gap-2 py-3 border border-ctx-teal/30 rounded-lg text-ctx-teal hover:bg-ctx-teal/10 transition-all"
          >
            <span className="font-bold text-sm uppercase tracking-wider font-rajdhani">
              Ver de dónde viene tu plata
            </span>
            <span className="material-symbols-outlined text-sm">chevron_right</span>
          </button>
        </div>
      </section>

      {/* Health Quadrant */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Plata Disponible */}
        <div className="bg-[#111827] border border-white/10 rounded-xl p-5 hover:border-emerald-500/30 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-xs font-rajdhani uppercase tracking-widest">Plata Disponible</h3>
            <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider">
              Bien
            </span>
          </div>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold text-white font-orbitron">$42.8M</div>
              <div className="text-xs text-gray-500 mt-1 font-mono">1.2x vs mes anterior</div>
            </div>
            <button className="text-gray-500 hover:text-emerald-400 transition-colors flex items-center text-[10px] uppercase font-bold">
              Ver <span className="material-symbols-outlined text-sm ml-1">chevron_right</span>
            </button>
          </div>
        </div>

        {/* Ganancia Real */}
        <div className="bg-[#111827] border border-white/10 rounded-xl p-5 hover:border-emerald-500/30 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-xs font-rajdhani uppercase tracking-widest">Tu Ganancia</h3>
            <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider">
              Bien
            </span>
          </div>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold text-white font-orbitron">$12.5M</div>
              <div className="text-xs text-gray-500 mt-1 font-mono">Margen: 32%</div>
            </div>
            <button className="text-gray-500 hover:text-emerald-400 transition-colors flex items-center text-[10px] uppercase font-bold">
              Ver <span className="material-symbols-outlined text-sm ml-1">chevron_right</span>
            </button>
          </div>
        </div>

        {/* Impuestos DIAN */}
        <div className="bg-[#111827] border border-orange-500/20 rounded-xl p-5 hover:border-orange-500/40 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-xs font-rajdhani uppercase tracking-widest">Provisión DIAN</h3>
            <span className="bg-orange-500/20 text-orange-400 text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider">
              Ojo
            </span>
          </div>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold text-white font-orbitron">$4.3M</div>
              <div className="text-xs text-orange-400/80 mt-1 font-mono">Reserva actual: $3M</div>
            </div>
            <button className="text-gray-500 hover:text-orange-400 transition-colors flex items-center text-[10px] uppercase font-bold">
              Resolver <span className="material-symbols-outlined text-sm ml-1">chevron_right</span>
            </button>
          </div>
        </div>

        {/* Costos Fijos */}
        <div className="bg-[#111827] border border-white/10 rounded-xl p-5 hover:border-blue-400/30 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-xs font-rajdhani uppercase tracking-widest">Costos Fijos</h3>
            <span className="bg-blue-400/20 text-blue-400 text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider">
              Estable
            </span>
          </div>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold text-white font-orbitron">$8.2M</div>
              <div className="text-xs text-gray-500 mt-1 font-mono">Cubierto por 3 meses</div>
            </div>
            <button className="text-gray-500 hover:text-blue-400 transition-colors flex items-center text-[10px] uppercase font-bold">
              Ver <span className="material-symbols-outlined text-sm ml-1">chevron_right</span>
            </button>
          </div>
        </div>
      </section>
      
      {/* Auditoría Sombra Banner */}
      <section className="bg-gradient-to-br from-ctx-violet/20 to-transparent border border-ctx-violet/30 rounded-xl p-5 flex items-center justify-between hover:border-ctx-violet/50 transition-all cursor-pointer group mt-4">
        <div className="flex flex-col gap-1">
          <h3 className="font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-ctx-violet">radar</span>
            Auditoría Sombra DIAN
          </h3>
          <p className="text-sm text-gray-400">
            Simula lo que ve la DIAN y evita multas antes de declarar.
          </p>
        </div>
        <span className="material-symbols-outlined text-ctx-violet group-hover:translate-x-1 transition-transform">
          arrow_forward
        </span>
      </section>

    </div>
  );
};
