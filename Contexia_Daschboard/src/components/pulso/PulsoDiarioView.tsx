import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { ShieldCheck, AlertTriangle, FileText, Activity, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

const PulsoMainCard = ({ data }: { data: any }) => {
  const isHealthy = data.kpis?.audit_risk_score < 0.3;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-card-elevated p-8 relative overflow-hidden border-2 ${
        isHealthy ? 'border-green-500/30 animate-glow-pulse' : 'border-red-500/30'
      }`}
    >
      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-2">
          <div className={`p-2 rounded-xl ${isHealthy ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
            <ShieldCheck className={`w-6 h-6 ${isHealthy ? 'text-green-400' : 'text-red-400'}`} />
          </div>
          <span className="font-rajdhani text-sm text-gray-400 uppercase tracking-widest">
            Health Status DIAN
          </span>
        </div>

        <motion.h2 className={`font-orbitron text-5xl md:text-6xl font-bold mb-3 ${isHealthy ? 'text-green-400' : 'text-red-400'}`}>
          {isHealthy ? 'SALUDABLE' : 'EN RIESGO'}
        </motion.h2>

        <p className="text-gray-400 text-sm flex items-center gap-2">
          {isHealthy ? (
            <span className="text-green-400 font-semibold">Tus operaciones fiscales están en regla.</span>
          ) : (
            <span className="text-red-400 font-semibold">Requiere atención inmediata de tu neurocontador.</span>
          )}
        </p>
      </div>
    </motion.div>
  );
};

const PulsoMetrics = ({ data }: { data: any }) => {
  const metrics = [
    {
      label: 'Tax Filings Pending',
      value: data.kpis?.tax_filings_pending || 0,
      icon: FileText,
      positive: data.kpis?.tax_filings_pending === 0,
      color: 'ctx-teal',
    },
    {
      label: 'Alerts Count',
      value: data.kpis?.alerts_count || 0,
      icon: AlertTriangle,
      positive: data.kpis?.alerts_count === 0,
      color: 'ctx-violet',
    },
    {
      label: 'Audit Risk Score',
      value: `${((data.kpis?.audit_risk_score || 0) * 100).toFixed(1)}%`,
      icon: Activity,
      positive: data.kpis?.audit_risk_score < 0.2,
      color: 'yellow-400',
    },
    {
      label: 'Compliance Status',
      value: String(data.kpis?.compliance_status || 'unknown').toUpperCase(),
      icon: ShieldCheck,
      positive: data.kpis?.compliance_status === 'green',
      color: 'green-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((m, i) => (
        <motion.div key={m.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * i }} className="stat-card p-5">
          <div className="flex justify-between items-start mb-3">
            <div className={`p-2 rounded-xl bg-white/5`}>
              <m.icon className={`w-5 h-5 text-${m.color}`} />
            </div>
          </div>
          <p className="text-gray-400 text-[10px] font-rajdhani uppercase tracking-widest mb-1">{m.label}</p>
          <h3 className="text-xl font-orbitron font-bold text-white">{m.value}</h3>
        </motion.div>
      ))}
    </div>
  );
};

export const PulsoDiarioView = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPulsoToday('31676930-b476-472b-bced-fd25f973cf8a')
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

  if (!data) return <div className="text-white text-center">Error cargando Pulso.</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PulsoMainCard data={data} />
      <PulsoMetrics data={data} />
    </div>
  );
};
