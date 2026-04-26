import { motion } from 'motion/react';
import { ShieldCheck, Clock, ChevronRight, Phone } from 'lucide-react';
import { MOCK_CENTINELA, MOCK_ALERTAS, formatCOP, type Severidad } from '../../data/mockData';

const sevConfig: Record<Severidad, { bg: string; border: string; text: string; dot: string; label: string }> = {
  roja: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-500', label: 'Crítico' },
  amarilla: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', dot: 'bg-yellow-500', label: 'Atención' },
  verde: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', dot: 'bg-green-500', label: 'Bien' },
};

const UmbralProgress = ({ nombre, progreso, severidad }: { nombre: string; progreso: number; severidad: Severidad }) => {
  const c = sevConfig[severidad];
  const capped = Math.min(progreso, 100);
  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-gray-400 font-rajdhani uppercase tracking-wider">{nombre}</span>
        <span className={`text-xs font-bold ${c.text}`}>{progreso}%{progreso > 100 && ' ⚠️'}</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${capped}%` }} transition={{ duration: 1 }}
          className={`h-full rounded-full ${progreso > 100 ? 'bg-red-500' : severidad === 'amarilla' ? 'bg-yellow-500' : 'bg-green-500'}`} />
      </div>
    </div>
  );
};

const AlertaCard = ({ alerta, index }: { alerta: typeof MOCK_ALERTAS[0]; index: number }) => {
  const c = sevConfig[alerta.severidad];
  return (
    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + index * 0.1 }}
      className={`glass-card p-6 ${c.border} ${c.bg} border-l-4`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${c.dot} animate-pulse`} />
          <span className={`text-[10px] font-bold uppercase tracking-widest ${c.text}`}>{c.label}</span>
        </div>
        {alerta.fecha_limite && (
          <div className="flex items-center gap-1 text-gray-500 text-xs">
            <Clock className="w-3 h-3" />
            <span>{new Date(alerta.fecha_limite).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
          </div>
        )}
      </div>
      <h3 className="text-white font-bold text-base mb-2">{alerta.titulo}</h3>
      <p className="text-gray-400 text-sm mb-4 leading-relaxed">{alerta.descripcion}</p>
      {alerta.porcentaje_progreso != null && alerta.umbral_nombre && (
        <UmbralProgress nombre={alerta.umbral_nombre} progreso={alerta.porcentaje_progreso} severidad={alerta.severidad} />
      )}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mt-4 pt-4 border-t border-white/5">
        <div className="flex items-start gap-2">
          <ChevronRight className="w-4 h-4 text-ctx-teal mt-0.5 flex-shrink-0" />
          <p className="text-ctx-teal text-sm">{alerta.accion_sugerida}</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-ctx-teal/10 border border-ctx-teal/20 rounded-xl text-ctx-teal text-xs font-bold uppercase tracking-wider hover:bg-ctx-teal/20 transition-all flex-shrink-0">
          <Phone className="w-3 h-3" /> Hablar con mi contador
        </button>
      </div>
    </motion.div>
  );
};

export const CentinelaView = () => {
  const rojas = MOCK_ALERTAS.filter(a => a.severidad === 'roja').length;
  const amarillas = MOCK_ALERTAS.filter(a => a.severidad === 'amarilla').length;
  const verdes = MOCK_ALERTAS.filter(a => a.severidad === 'verde').length;
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-ctx-violet/20"><ShieldCheck className="w-6 h-6 text-ctx-violet" /></div>
          <p className="text-gray-400 text-xs font-rajdhani uppercase tracking-widest">Tu escudo preventivo contra sorpresas DIAN</p>
        </div>
      </motion.div>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { emoji: '🔴', count: rojas, label: 'Críticas', color: 'red' },
          { emoji: '🟡', count: amarillas, label: 'Atención', color: 'yellow' },
          { emoji: '🟢', count: verdes, label: 'Todo bien', color: 'green' },
        ].map(s => (
          <div key={s.label} className={`glass-card p-4 border-${s.color}-500/20 flex items-center gap-4`}>
            <div className={`w-10 h-10 rounded-xl bg-${s.color}-500/20 flex items-center justify-center`}><span className="text-lg">{s.emoji}</span></div>
            <div>
              <p className={`text-2xl font-orbitron font-bold text-${s.color}-400`}>{s.count}</p>
              <p className="text-[10px] text-gray-400 uppercase tracking-widest">{s.label}</p>
            </div>
          </div>
        ))}
      </motion.div>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest font-rajdhani">Ingresos acumulados este año</p>
            <p className="text-2xl font-orbitron font-bold text-white">{formatCOP(MOCK_CENTINELA.ingresos_acumulados_ytd)}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-gray-400 uppercase tracking-widest font-rajdhani">Fecha evaluación</p>
            <p className="text-sm text-gray-300">{new Date(MOCK_CENTINELA.fecha_evaluacion).toLocaleDateString('es-CO')}</p>
          </div>
        </div>
      </motion.div>
      <div className="space-y-4">
        {MOCK_ALERTAS.map((a, i) => <AlertaCard key={a.id} alerta={a} index={i} />)}
      </div>
    </div>
  );
};
