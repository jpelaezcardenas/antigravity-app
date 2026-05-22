import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { ShieldCheck, Clock, ChevronRight, Phone, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

type BackendSeverity = 'critical' | 'warning' | 'info';
const sevConfig: Record<BackendSeverity, { bg: string; border: string; text: string; dot: string; label: string }> = {
  critical: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-500', label: 'Crítico' },
  warning: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', dot: 'bg-yellow-500', label: 'Atención' },
  info: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', dot: 'bg-green-500', label: 'Info' },
};



const AlertaCard = ({ alerta, index }: { alerta: any; index: number }) => {
  const c = sevConfig[alerta.severity as BackendSeverity] || sevConfig['info'];
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
      <h3 className="text-white font-bold text-base mb-2">{alerta.type}</h3>
      <p className="text-gray-400 text-sm mb-4 leading-relaxed">{alerta.message}</p>
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mt-4 pt-4 border-t border-white/5">
        <div className="flex items-start gap-2">
          <ChevronRight className="w-4 h-4 text-ctx-teal mt-0.5 flex-shrink-0" />
          <p className="text-ctx-teal text-sm">Requiere acción o revisión contable</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-ctx-teal/10 border border-ctx-teal/20 rounded-xl text-ctx-teal text-xs font-bold uppercase tracking-wider hover:bg-ctx-teal/20 transition-all flex-shrink-0">
          <Phone className="w-3 h-3" /> Hablar con mi contador
        </button>
      </div>
    </motion.div>
  );
};

export const CentinelaView = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userStr = localStorage.getItem('cx_user');
    let userId = 'demo-uuid-1234-5678';
    if (userStr) {
      const user = JSON.parse(userStr);
      userId = user.id || user.usuario_id || userId;
    }

    api.getCentinelaAlerts(userId)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-ctx-teal animate-spin" />
      </div>
    );
  }

  if (!data) return <div className="text-white text-center">No se pudieron cargar las alertas.</div>;

  const getSeverity = (sev: string): 'critical' | 'warning' | 'info' => {
    if (sev === 'roja') return 'critical';
    if (sev === 'amarilla') return 'warning';
    return 'info';
  };

  const getMessage = (alerta: any) => {
    if (alerta.dias_estimados) {
      return `Alcanzarás este umbral en aproximadamente ${alerta.dias_estimados} días al ritmo actual (${alerta.porcentaje}% de ${alerta.umbral.toLocaleString('es-CO')}).`;
    }
    return `Estado actual: ${alerta.porcentaje}% del umbral de ${alerta.umbral.toLocaleString('es-CO')}.`;
  };

  // The backend returns an array of alerts directly
  const todasLasAlertas = Array.isArray(data) ? data.map((a: any) => ({
    type: a.nombre,
    message: getMessage(a),
    severity: getSeverity(a.severidad),
    fecha_limite: new Date(new Date().setDate(new Date().getDate() + (a.dias_estimados || 30))).toISOString(),
  })) : [];

  const rojas = todasLasAlertas.filter((a: any) => a.severity === 'critical').length;
  const amarillas = todasLasAlertas.filter((a: any) => a.severity === 'warning').length;
  const verdes = todasLasAlertas.filter((a: any) => a.severity === 'info').length;

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
          { emoji: '🟢', count: verdes, label: 'Info', color: 'green' },
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
      <div className="space-y-4">
        {todasLasAlertas.length === 0 && <p className="text-green-400 text-center mt-10">Cero alertas fiscales. Estás al día.</p>}
        {todasLasAlertas.map((a: any, i: number) => <AlertaCard key={a.id || i} alerta={a} index={i} />)}
      </div>
    </div>
  );
};
