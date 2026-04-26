import { motion } from 'motion/react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Wallet, ShieldCheck, DollarSign, AlertTriangle } from 'lucide-react';
import { MOCK_PULSO, formatCOP, formatCOPShort } from '../../data/mockData';

const PulsoMainCard = () => {
  const isPositive = MOCK_PULSO.dinero_tuyo_hoy >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className={`glass-card p-8 relative overflow-hidden border-2 ${
        isPositive ? 'border-green-500/30' : 'border-red-500/30'
      }`}
    >
      {/* Background gradient */}
      <div
        className={`absolute inset-0 ${
          isPositive
            ? 'bg-gradient-to-br from-green-500/10 via-transparent to-ctx-teal/5'
            : 'bg-gradient-to-br from-red-500/10 via-transparent to-red-900/5'
        }`}
      />

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-2">
          <div className={`p-2 rounded-xl ${isPositive ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
            <Wallet className={`w-6 h-6 ${isPositive ? 'text-green-400' : 'text-red-400'}`} />
          </div>
          <span className="font-rajdhani text-sm text-gray-400 uppercase tracking-widest">
            Tu dinero hoy
          </span>
        </div>

        <motion.h2
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}
          className={`font-orbitron text-5xl md:text-6xl font-bold mb-3 ${
            isPositive ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {formatCOP(MOCK_PULSO.dinero_tuyo_hoy)}
        </motion.h2>

        <p className="text-gray-400 text-sm flex items-center gap-2">
          {isPositive ? (
            <>
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-green-400 font-semibold">Puedes gastar sin miedo a la DIAN</span>
            </>
          ) : (
            <>
              <TrendingDown className="w-4 h-4 text-red-400" />
              <span className="text-red-400 font-semibold">Atención: revisa tus gastos</span>
            </>
          )}
        </p>

        <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 bg-ctx-teal rounded-full animate-pulse" />
          Última sincronización: hace unos minutos
        </div>
      </div>
    </motion.div>
  );
};

const PulsoMetrics = () => {
  const metrics = [
    {
      label: 'Ventas Ayer',
      value: formatCOP(MOCK_PULSO.ventas_ayer),
      icon: TrendingUp,
      change: '+12.3%',
      positive: true,
      color: 'ctx-teal',
    },
    {
      label: 'Gastos Ayer',
      value: formatCOP(MOCK_PULSO.gastos_ayer),
      icon: TrendingDown,
      change: '-3.1%',
      positive: true,
      color: 'ctx-violet',
    },
    {
      label: 'Margen Bruto',
      value: formatCOP(MOCK_PULSO.margen_bruto),
      icon: DollarSign,
      change: `${((MOCK_PULSO.margen_bruto / MOCK_PULSO.ingresos_brutos) * 100).toFixed(1)}%`,
      positive: true,
      color: 'green-400',
    },
    {
      label: 'Provisión DIAN',
      value: formatCOP(MOCK_PULSO.provision_dian),
      icon: ShieldCheck,
      change: `${MOCK_PULSO.porcentaje_tributario_estimado}% est.`,
      positive: false,
      color: 'yellow-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((m, i) => (
        <motion.div
          key={m.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 + i * 0.1 }}
          whileHover={{ translateY: -4 }}
          className="glass-card p-5 group hover:border-ctx-teal/20 transition-all"
        >
          <div className="flex justify-between items-start mb-3">
            <div className={`p-2 rounded-xl bg-white/5 group-hover:bg-${m.color}/10 transition-colors`}>
              <m.icon className={`w-5 h-5 text-${m.color}`} />
            </div>
            <span
              className={`text-xs font-bold font-rajdhani ${
                m.positive ? 'text-green-400' : 'text-yellow-400'
              }`}
            >
              {m.change}
            </span>
          </div>
          <p className="text-gray-400 text-[10px] font-rajdhani uppercase tracking-widest mb-1">
            {m.label}
          </p>
          <h3 className="text-xl font-orbitron font-bold text-white">{m.value}</h3>
        </motion.div>
      ))}
    </div>
  );
};

const PulsoChart = () => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.5 }}
    className="glass-card p-6"
  >
    <div className="flex items-center justify-between mb-6">
      <div>
        <h3 className="font-orbitron text-lg text-white">Tendencia 30 días</h3>
        <p className="text-gray-500 text-xs font-rajdhani uppercase tracking-widest">
          Tu dinero disponible día a día
        </p>
      </div>
      <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5">
        <div className="w-3 h-1 rounded-full bg-ctx-teal" />
        <span className="text-[10px] text-gray-400 uppercase tracking-wider">Dinero tuyo</span>
      </div>
    </div>

    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={MOCK_PULSO.tendencia_30_dias}>
          <defs>
            <linearGradient id="colorPulso" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="fecha"
            stroke="rgba(255,255,255,0.3)"
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          />
          <YAxis
            stroke="rgba(255,255,255,0.3)"
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
            tickFormatter={(v) => `$${(v / 1_000_000).toFixed(1)}M`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1E293B',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              color: '#fff',
              fontSize: '12px',
            }}
            formatter={(value: number) => [formatCOP(value), 'Dinero tuyo']}
          />
          <Area
            type="monotone"
            dataKey="valor"
            stroke="#2DD4BF"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPulso)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </motion.div>
);

const PulsoAdvertencias = () => {
  if (MOCK_PULSO.advertencias.length === 0) return null;
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 flex items-start gap-3"
    >
      <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-yellow-400 font-bold text-sm mb-1">Datos incompletos</p>
        {MOCK_PULSO.advertencias.map((adv, i) => (
          <p key={i} className="text-yellow-400/70 text-xs">{adv}</p>
        ))}
      </div>
    </motion.div>
  );
};

export const PulsoDiarioView = () => (
  <div className="space-y-6 max-w-7xl mx-auto">
    <PulsoAdvertencias />
    <PulsoMainCard />
    <PulsoMetrics />
    <PulsoChart />
  </div>
);
