import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  LayoutDashboard, Wallet, ShieldCheck, Radar, Receipt,
  MessageSquare, Settings, TrendingUp, AlertTriangle,
  ArrowUpRight, ArrowDownRight, ChevronRight, Bell,
  Search, LogOut, Globe, Zap, Target, Menu, X,
  PieChart, Building2, Users, ArrowLeft
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { MOCK_USER, MOCK_PULSO, MOCK_CLIENTS, DEMO_CREDENTIALS, ClienteActivo, formatCOP, formatCOPShort } from './data/mockData';
import { PulsoDiarioView } from './components/pulso/PulsoDiarioView';
import { CentinelaView } from './components/centinela/CentinelaView';
import { ComingSoonView } from './components/shared/ComingSoonView';
import { TatyView } from './components/taty/TatyView';
import { ConfiguracionView } from './components/configuracion/ConfiguracionView';

const chartData = [
  { name: '1', ingresos: 4000, egresos: 2400 },
  { name: '5', ingresos: 3000, egresos: 1398 },
  { name: '10', ingresos: 2000, egresos: 8000 },
  { name: '15', ingresos: 2780, egresos: 3908 },
  { name: '20', ingresos: 6890, egresos: 4800 },
  { name: '25', ingresos: 5390, egresos: 3800 },
  { name: '30', ingresos: 8490, egresos: 4300 },
];

const navItems = [
  { id: 'inicio', label: 'Inicio', icon: LayoutDashboard },
  { id: 'pulso', label: 'Pulso Diario', icon: Wallet },
  { id: 'centinela', label: 'Centinela Fiscal', icon: ShieldCheck },
  { id: 'auditoria', label: 'Auditoría Sombra', icon: Search },
  { id: 'radar', label: 'Radar Predictivo', icon: Radar },
  { id: 'configuracion', label: 'Configuración', icon: Settings },
];

// --- Sub-components ---

const StatCard = ({ icon: Icon, label, value, change, positive }: any) => (
  <motion.div whileHover={{ translateY: -5 }}
    className="glass-card p-6 border-white/5 hover:border-ctx-teal/20 transition-all group">
    <div className="flex justify-between items-start mb-4">
      <div className="p-3 rounded-2xl bg-white/5 group-hover:bg-ctx-teal/10 transition-colors">
        <Icon className="w-6 h-6 text-ctx-teal" />
      </div>
      <div className={`flex items-center gap-1 text-xs font-bold font-rajdhani ${positive ? 'text-green-400' : 'text-red-400'}`}>
        {positive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
        {change}
      </div>
    </div>
    <p className="text-gray-400 text-xs font-rajdhani uppercase tracking-wider mb-1">{label}</p>
    <h3 className="text-2xl font-orbitron font-bold text-white">{value}</h3>
  </motion.div>
);

const AlertItem = ({ type, title, desc }: any) => {
  const colors: any = {
    danger: 'text-red-400 border-red-500/20 bg-red-500/5',
    warning: 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5',
    info: 'text-blue-400 border-blue-500/20 bg-blue-500/5'
  };
  return (
    <div className={`p-3 rounded-xl border ${colors[type] || colors.info}`}>
      <h4 className="text-sm font-bold mb-1">{title}</h4>
      <p className="text-xs text-gray-400">{desc}</p>
    </div>
  );
};

const SidebarContent = ({ activeTab, setActiveTab, onLogout, onClose, onBackToBunker }: any) => (
  <>
    <div className="flex items-center justify-between mb-8 px-2">
      <a href="https://wa.me/573018948151" target="_blank" rel="noopener noreferrer" 
         className="w-full flex items-center justify-center gap-2 bg-[#25D366] hover:bg-[#20bd5a] text-white py-2.5 px-3 rounded-full transition-transform hover:scale-105 shadow-[0_0_15px_rgba(37,211,102,0.3)]">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
          <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z"/>
        </svg>
        <span className="text-[10px] font-bold font-rajdhani uppercase tracking-wider text-center leading-none">Tu Amiga Contadora<br/>Taty 24/7</span>
      </a>
      {onClose && <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg lg:hidden ml-2"><X className="w-5 h-5 text-gray-400" /></button>}
    </div>
    <nav className="space-y-1 flex-1">
      {navItems.map((item) => (
        <button key={item.id}
          onClick={() => { 
            if (item.id === 'auditoria') {
              window.location.href = '/wizard/';
              return;
            }
            setActiveTab(item.id); 
            onClose?.(); 
          }}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all relative group ${
            activeTab === item.id
              ? 'bg-ctx-teal/10 text-ctx-teal border border-ctx-teal/20'
              : 'text-gray-400 hover:bg-white/5 hover:text-white'
          }`}>
          {activeTab === item.id && (
            <motion.div layoutId="activeNav"
              className="absolute left-[-24px] w-1 h-8 bg-ctx-teal rounded-r-full shadow-[0_0_15px_rgba(45,212,191,0.5)]" />
          )}
          <item.icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${activeTab === item.id ? 'text-ctx-teal' : 'text-gray-500'}`} />
          <span className="font-rajdhani text-sm uppercase tracking-widest font-semibold">{item.label}</span>
          {item.id === 'auditoria' && (
            <div className="absolute right-3 px-1.5 py-0.5 bg-ctx-teal/20 text-ctx-teal text-[8px] font-black rounded border border-ctx-teal/30 animate-pulse">GRATIS</div>
          )}
        </button>
      ))}
    </nav>
    <div className="mt-auto pt-4 flex flex-col gap-4">
      <div className="flex flex-col items-center justify-center py-4 mb-2">
        <p className="font-rajdhani text-[10px] text-gray-500 uppercase tracking-widest mb-3">
          Powered by Contexia
        </p>
        <img src="/assets/img/logo_official_transparent.png" alt="Contexia" className="h-28 object-contain opacity-90 hover:opacity-100 transition-opacity drop-shadow-[0_0_8px_rgba(45,212,191,0.2)]" />
      </div>
      {onBackToBunker && (
        <button onClick={onBackToBunker}
          className="w-full flex items-center gap-3 px-4 py-3 text-ctx-teal hover:bg-ctx-teal/10 rounded-xl transition-colors group border border-ctx-teal/20 mb-2">
          <ArrowLeft className="w-5 h-5 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-rajdhani uppercase tracking-widest font-bold">Volver al Búnker</span>
        </button>
      )}
      <button onClick={onLogout}
        className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:text-red-400 transition-colors group border-t border-white/5 mt-2">
        <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
        <span className="text-sm font-rajdhani uppercase tracking-widest font-bold">Cerrar Sesión</span>
      </button>
    </div>
  </>
);

const DashboardHome = ({ setActiveTab, clienteNombre }: { setActiveTab: (t: string) => void; clienteNombre: string }) => (
  <>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <StatCard icon={TrendingUp} label="Ingresos" value={formatCOPShort(MOCK_PULSO.ingresos_brutos)} change="+5.2%" positive />
      <StatCard icon={Wallet} label="Caja Real (Hoy)" value={formatCOPShort(MOCK_PULSO.dinero_tuyo_hoy)} change="+8.1%" positive />
      <StatCard icon={ShieldCheck} label="Provisión DIAN" value={formatCOPShort(MOCK_PULSO.provision_dian)} change="Fija" positive />
      <StatCard icon={Radar} label="Margen" value={`${((MOCK_PULSO.margen_bruto / MOCK_PULSO.ingresos_brutos) * 100).toFixed(1)}%`} change="+2%" positive />
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
      <div className="lg:col-span-2 space-y-8">
        <div className="glass-card p-6 h-[350px] border-ctx-teal/20">
          <h3 className="font-orbitron text-lg mb-4">Flujo de Caja — 30 días</h3>
          <ResponsiveContainer width="100%" height="85%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorIng" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorEgr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1D4ED8" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#1D4ED8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
              <YAxis stroke="rgba(255,255,255,0.3)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
              <Area type="monotone" dataKey="ingresos" stroke="#3B82F6" fillOpacity={1} fill="url(#colorIng)" />
              <Area type="monotone" dataKey="egresos" stroke="#1D4ED8" fillOpacity={1} fill="url(#colorEgr)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card p-6 border-ctx-violet/20">
            <h3 className="font-orbitron text-lg mb-4 flex items-center gap-2"><Zap className="w-5 h-5 text-ctx-violet" /> Acciones Rápidas</h3>
            <div className="space-y-3">
              {[
                { label: 'Ver Pulso Diario', tab: 'pulso' },
                { label: 'Revisar Alertas DIAN', tab: 'centinela' },
                { label: 'Ejecutar Auditoría Sombra', tab: 'auditoria' },
              ].map(a => (
                <button key={a.tab} 
                  onClick={() => {
                    if (a.tab === 'auditoria') {
                      window.location.href = '/wizard/';
                      return;
                    }
                    setActiveTab(a.tab);
                  }}
                  className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors flex items-center justify-between group">
                  <span className="text-sm">{a.label}</span>
                  <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-ctx-violet transition-colors" />
                </button>
              ))}
            </div>
          </div>
          <div className="glass-card p-6 border-ctx-teal/20">
            <h3 className="font-orbitron text-lg mb-4 flex items-center gap-2"><Target className="w-5 h-5 text-ctx-teal" /> Metas Financieras</h3>
            <div className="space-y-4">
              {[{ label: 'Reserva de Caja', pct: 85, color: 'bg-ctx-teal' }, { label: 'Optimización Impuestos', pct: 62, color: 'bg-ctx-violet' }].map(g => (
                <div key={g.label}>
                  <div className="flex justify-between text-xs mb-1 uppercase tracking-tighter text-gray-400">
                    <span>{g.label}</span><span>{g.pct}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full ${g.color}`} style={{ width: `${g.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="space-y-8">
        <div className="glass-card p-6 border-white/10 bg-navy-light/30">
          <h3 className="font-orbitron text-lg mb-6">Alertas Críticas</h3>
          <div className="space-y-4">
            <AlertItem type="danger" title="Desviación en Pauta (CAC)" desc="El costo de adquisición en Meta Ads excede el margen en 15%" />
            <AlertItem type="warning" title="Vencimiento IVA (Bimestral)" desc="Plazo límite para declarar IVA de ventas en 3 días" />
            <AlertItem type="info" title="Nueva Oportunidad Fiscal" desc="Deducción identificada en comisiones de pasarela (Stripe/Wompi)" />
          </div>
        </div>
        <div className="glass-card p-6 border-ctx-teal/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10"><Globe className="w-20 h-20" /></div>
          <h3 className="font-orbitron text-lg mb-2">{clienteNombre}</h3>
          <p className="text-sm text-gray-400 mb-4">Tu empresa opera bajo estándares internacionales.</p>
          <div className="flex gap-2">
            <div className="px-2 py-1 bg-ctx-teal/10 text-ctx-teal text-[10px] rounded uppercase font-bold tracking-widest">NIIF</div>
            <div className="px-2 py-1 bg-ctx-violet/10 text-ctx-violet text-[10px] rounded uppercase font-bold tracking-widest">DIAN</div>
          </div>
        </div>
      </div>
    </div>
  </>
);

// --- Búnker Admin View ---

const estadoColor: Record<string, string> = {
  verde: 'text-green-400 bg-green-500/10 border-green-500/30',
  ambar: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  rojo: 'text-red-400 bg-red-500/10 border-red-500/30',
};

const estadoDot: Record<string, string> = {
  verde: 'bg-green-400',
  ambar: 'bg-yellow-400',
  rojo: 'bg-red-400',
};

const ClientCard = ({ cliente, onSelect }: { cliente: ClienteActivo; onSelect: () => void }) => (
  <motion.div
    whileHover={{ translateY: -4 }}
    className="glass-card p-6 border-white/5 hover:border-ctx-teal/20 transition-all cursor-pointer group"
    onClick={onSelect}
  >
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-white/5 group-hover:bg-ctx-teal/10 transition-colors">
          <Building2 className="w-5 h-5 text-ctx-teal" />
        </div>
        <div>
          <h3 className="font-orbitron font-bold text-white text-sm leading-tight">{cliente.nombre}</h3>
          <p className="text-[10px] text-gray-500 font-rajdhani uppercase tracking-widest mt-0.5">{cliente.sector}</p>
        </div>
      </div>
      <span className={`flex items-center gap-1.5 px-2 py-1 rounded-full border text-[10px] font-bold font-rajdhani uppercase ${estadoColor[cliente.estado]}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${estadoDot[cliente.estado]}`} />
        {cliente.estado}
      </span>
    </div>

    <div className="grid grid-cols-3 gap-3 mb-4">
      {[
        { label: 'Ingresos/mes', value: formatCOPShort(cliente.ingresos_mes) },
        { label: 'Caja hoy', value: formatCOPShort(cliente.caja_hoy) },
        { label: 'Prov. DIAN', value: formatCOPShort(cliente.provision_dian) },
      ].map(stat => (
        <div key={stat.label} className="bg-white/5 rounded-lg p-2 text-center">
          <p className="text-[9px] text-gray-500 font-rajdhani uppercase tracking-wider mb-0.5">{stat.label}</p>
          <p className="text-xs font-bold font-orbitron text-white">{stat.value}</p>
        </div>
      ))}
    </div>

    <div className="space-y-1.5 mb-4">
      <div className="flex items-start gap-2">
        <AlertTriangle className="w-3 h-3 text-gray-500 mt-0.5 shrink-0" />
        <p className="text-[11px] text-gray-400">{cliente.ultima_alerta}</p>
      </div>
      <div className="flex items-start gap-2">
        <ChevronRight className="w-3 h-3 text-ctx-teal mt-0.5 shrink-0" />
        <p className="text-[11px] text-ctx-teal">{cliente.proxima_accion}</p>
      </div>
    </div>

    <button className="w-full py-2 rounded-xl bg-ctx-teal/10 hover:bg-ctx-teal/20 text-ctx-teal text-xs font-bold font-rajdhani uppercase tracking-widest transition-colors border border-ctx-teal/20 group-hover:border-ctx-teal/40">
      Ver Portal →
    </button>
  </motion.div>
);

const BunkerView = ({
  onSelectClient,
  onLogout,
}: {
  onSelectClient: (id: string) => void;
  onLogout: () => void;
}) => (
  <div className="min-h-screen bg-navy-dark text-white">
    <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 lg:px-10 bg-navy-dark/80 backdrop-blur-md sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <img src="/assets/img/logo_official_transparent.png" alt="Contexia" className="h-8 object-contain opacity-90" />
        <div className="w-px h-5 bg-white/10" />
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 bg-ctx-teal rounded-full animate-pulse" />
          <span className="text-[10px] font-rajdhani uppercase tracking-widest text-gray-400">Búnker Admin</span>
        </div>
      </div>
      <button
        onClick={onLogout}
        className="flex items-center gap-2 text-gray-500 hover:text-red-400 transition-colors text-xs font-rajdhani uppercase tracking-widest"
      >
        <LogOut className="w-4 h-4" />
        Cerrar Sesión
      </button>
    </header>

    <main className="p-6 lg:p-10 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="font-orbitron text-2xl lg:text-3xl font-bold text-white mb-1">
          Búnker <span className="text-ctx-teal">Contexia</span>
        </h1>
        <p className="text-gray-400 font-rajdhani text-sm uppercase tracking-wider">
          {MOCK_CLIENTS.length} clientes activos · Vista de gestión interna
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
        {MOCK_CLIENTS.map(cliente => (
          <ClientCard key={cliente.id} cliente={cliente} onSelect={() => onSelectClient(cliente.id)} />
        ))}
      </div>
    </main>
  </div>
);

// --- Login View ---

const LoginView = ({ onLogin }: { onLogin: (role: 'admin' | 'client') => void }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const isAdmin = email === DEMO_CREDENTIALS.admin.email && password === DEMO_CREDENTIALS.admin.password;
    const isClient = email === DEMO_CREDENTIALS.cliente.email && password === DEMO_CREDENTIALS.cliente.password;
    if (!isAdmin && !isClient) {
      setError('Credenciales incorrectas. Usa las credenciales demo.');
      return;
    }
    setLoading(true);
    setTimeout(() => { setLoading(false); onLogin(isAdmin ? 'admin' : 'client'); }, 700);
  };

  return (
    <div className="min-h-screen bg-navy-dark flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-ctx-teal/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-ctx-violet/10 blur-[120px] rounded-full" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-md w-full relative z-10">
        <div className="text-center mb-10">
          <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="flex flex-col items-center justify-center gap-2 mb-6">
            <img src="/assets/img/logo_official_transparent.png" alt="Contexia" className="h-20 object-contain drop-shadow-[0_0_20px_rgba(45,212,191,0.3)]" />
            <span className="font-rajdhani text-sm text-ctx-teal tracking-[0.3em] uppercase font-semibold">Portal de Clientes</span>
          </motion.div>
          <h2 className="text-lg text-gray-400 font-rajdhani uppercase tracking-widest">GPS Financiero para PyMEs</h2>
        </div>
        <div className="glass-card p-8 border-white/10">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-rajdhani uppercase tracking-widest text-gray-400 mb-2">Email</label>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                  placeholder="usuario@empresa.com" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-rajdhani uppercase tracking-widest text-gray-400 mb-2">Contraseña</label>
              <div className="relative">
                <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                  placeholder="••••••••" />
              </div>
            </div>
            {error && (
              <p className="text-red-400 text-xs text-center font-rajdhani">{error}</p>
            )}
            <div className="bg-white/3 border border-white/8 rounded-xl p-4 space-y-2">
              <p className="text-gray-500 text-[10px] font-rajdhani uppercase tracking-widest text-center mb-1">Acceso Demo</p>
              <div className="grid grid-cols-2 gap-2">
                <button type="button" onClick={() => { setEmail(DEMO_CREDENTIALS.admin.email); setPassword(DEMO_CREDENTIALS.admin.password); }}
                  className="py-2 px-3 rounded-lg bg-ctx-teal/10 border border-ctx-teal/20 hover:bg-ctx-teal/20 transition-colors text-center">
                  <p className="text-ctx-teal text-[9px] font-black font-rajdhani uppercase tracking-widest">Admin</p>
                  <p className="text-gray-400 text-[9px] font-rajdhani truncate">admin@contexia.co</p>
                </button>
                <button type="button" onClick={() => { setEmail(DEMO_CREDENTIALS.cliente.email); setPassword(DEMO_CREDENTIALS.cliente.password); }}
                  className="py-2 px-3 rounded-lg bg-ctx-violet/10 border border-ctx-violet/20 hover:bg-ctx-violet/20 transition-colors text-center">
                  <p className="text-ctx-violet text-[9px] font-black font-rajdhani uppercase tracking-widest">Cliente</p>
                  <p className="text-gray-400 text-[9px] font-rajdhani truncate">cliente@demo.co</p>
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="premium-button w-full flex items-center justify-center gap-2 py-4">
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><span>Ingresar</span><ChevronRight className="w-4 h-4" /></>}
            </button>
          </form>
          <div className="mt-6 pt-5 border-t border-white/5 text-center">
            <p className="text-xs text-gray-500 font-rajdhani uppercase tracking-widest">
              ¿No tienes cuenta? <a href="/landing.html#contact" className="text-ctx-teal hover:underline">Solicitar Acceso</a>
            </p>
          </div>
        </div>
        <p className="mt-6 text-center text-[10px] text-gray-600 font-rajdhani uppercase tracking-[0.2em]">Contexia · GPS Financiero · v2.1.0</p>
      </motion.div>
    </div>
  );
};

// --- Main App ---

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [authState, setAuthState] = useState<'login' | 'admin' | 'client'>('login');
  const [activeClientId, setActiveClientId] = useState<string>('c6');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('inicio');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('cx_user');
    if (saved) {
      const parsed = JSON.parse(saved);
      setUser(parsed);
      setAuthState(parsed.role === 'admin' ? 'admin' : 'client');
      if (parsed.activeClientId) setActiveClientId(parsed.activeClientId);
    }
    setLoading(false);
  }, []);

  const handleLogin = (role: 'admin' | 'client') => {
    const userData = { ...MOCK_USER, role };
    localStorage.setItem('cx_user', JSON.stringify(userData));
    localStorage.setItem('token', MOCK_USER.token);
    setUser(userData);
    setAuthState(role);
  };

  const handleSelectClient = (clientId: string) => {
    setActiveClientId(clientId);
    setAuthState('client');
    setActiveTab('inicio');
    const updated = { ...user, activeClientId: clientId };
    setUser(updated);
    localStorage.setItem('cx_user', JSON.stringify(updated));
  };

  const handleBackToBunker = () => {
    setAuthState('admin');
    setActiveTab('inicio');
  };

  const handleLogout = () => {
    localStorage.removeItem('cx_user');
    localStorage.removeItem('token');
    setUser(null);
    setAuthState('login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-dark flex items-center justify-center">
        <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="text-center">
          <div className="w-16 h-16 border-4 border-ctx-teal border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-orbitron text-ctx-teal tracking-widest uppercase text-sm">Cargando...</p>
        </motion.div>
      </div>
    );
  }

  if (!user || authState === 'login') return <LoginView onLogin={handleLogin} />;
  if (authState === 'admin') return <BunkerView onSelectClient={handleSelectClient} onLogout={handleLogout} />;

  const activeClient = MOCK_CLIENTS.find(c => c.id === activeClientId) ?? MOCK_CLIENTS[5];

  const tabTitles: Record<string, string> = {
    inicio: 'Panel de Control',
    pulso: '📊 Pulso Diario',
    centinela: '🛡️ Centinela Fiscal',
    taty: '💬 Tu Amiga Contadora Taty',
    auditoria: '🔍 Auditoría Sombra',
    radar: '📡 Radar Predictivo',
    configuracion: '⚙️ Configuración',
  };

  const renderTab = () => {
    switch (activeTab) {
      case 'inicio': return <DashboardHome setActiveTab={setActiveTab} clienteNombre={activeClient.nombre} />;
      case 'pulso': return <PulsoDiarioView />;
      case 'centinela': return <CentinelaView />;
      case 'taty': return <TatyView />;
      case 'auditoria': {
        // Redirect immediately to the live wizard
        window.location.href = '/wizard/';
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-10 h-10 border-2 border-ctx-teal border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400 text-sm">Redirigiendo a Auditoría Sombra...</p>
            </div>
          </div>
        );
      }
      case 'radar': return (
        <ComingSoonView icon="radar" titulo="Radar Predictivo"
          subtitulo="Adelántate a tus impuestos"
          descripcion="Predicción de caja y carga tributaria de los próximos 90 días con Machine Learning. Sabrás cuánto deberás antes de que llegue la fecha."
          features={['ML Predictivo', 'Proyección 90 días', 'Escenarios múltiples', 'Alertas tempranas']} />
      );
      case 'configuracion': return <ConfiguracionView />;
      default: return <DashboardHome setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-navy-dark text-white flex font-sans selection:bg-ctx-teal/30">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-72 bg-navy-light/50 backdrop-blur-xl border-r border-white/5 flex-col p-6 fixed h-screen z-30">
        <SidebarContent activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout}
          onBackToBunker={user?.role === 'admin' ? handleBackToBunker : undefined} />
      </aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden" onClick={() => setMobileMenuOpen(false)} />
            <motion.aside initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }} transition={{ type: 'spring', damping: 25 }}
              className="fixed left-0 top-0 h-screen w-72 bg-navy-light/95 backdrop-blur-xl border-r border-white/5 flex flex-col p-6 z-50 lg:hidden">
              <SidebarContent activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} onClose={() => setMobileMenuOpen(false)}
                onBackToBunker={user?.role === 'admin' ? handleBackToBunker : undefined} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 lg:ml-72">
        {/* Top Nav */}
        <header className="h-16 lg:h-20 border-b border-white/5 flex items-center justify-between px-4 lg:px-8 bg-navy-dark/50 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileMenuOpen(true)} className="p-2 hover:bg-white/10 rounded-xl lg:hidden">
              <Menu className="w-5 h-5 text-gray-400" />
            </button>
            <div className="hidden sm:block relative w-64 lg:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input type="text" placeholder="Buscar..."
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-ctx-teal/50" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden md:flex bg-white/5 border border-white/10 rounded-full px-3 py-1.5 items-center gap-2">
              <div className="w-2 h-2 bg-ctx-teal rounded-full animate-pulse" />
              <span className="text-[10px] font-rajdhani uppercase tracking-wider text-gray-300">En línea</span>
            </div>
            <button className="p-2 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors relative">
              <Bell className="w-4 h-4 text-gray-400" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-ctx-violet rounded-full" />
            </button>
            <div className="flex items-center gap-4">
              <div className="hidden sm:block text-right pr-6 border-r border-white/10">
                <p className="text-sm font-bold text-white leading-none mb-1">{activeClient.nombre}</p>
                <p className="text-[10px] text-ctx-teal uppercase tracking-[0.2em] font-bold">Starter</p>
              </div>

              <button onClick={() => setActiveTab('taty')} className="relative group flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-2 pr-6 hover:bg-white/10 hover:border-ctx-teal/30 transition-all duration-500 cursor-pointer text-left" style={{ boxShadow: '0 0 20px rgba(45, 212, 191, 0.1)' }}>
                <div className="relative w-14 h-20 rounded-xl overflow-hidden border border-white/20 shadow-xl">
                  <img src="/assets/img/profiles/tatiana_full.png" alt="Taty" className="w-full h-full object-cover object-top group-hover:scale-110 transition-transform duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-navy-dark/60 via-transparent to-transparent"></div>
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-ctx-teal opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-ctx-teal"></span>
                    </span>
                    <span className="text-[10px] text-ctx-teal font-black uppercase tracking-widest leading-none">Online</span>
                  </div>
                  <span className="text-sm text-white font-bold leading-tight">Tu Amiga Contadora<br/><span className="text-ctx-teal group-hover:text-white transition-colors">Taty</span></span>
                </div>
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 custom-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div key={activeTab} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h1 className="text-2xl md:text-3xl font-orbitron font-bold text-white mb-1">
                    {activeTab === 'inicio' ? (
                      <>Bienvenido, <span className="text-ctx-teal">{activeClient.nombre}</span></>
                    ) : (
                      tabTitles[activeTab]
                    )}
                  </h1>
                </div>
              </div>
              {renderTab()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      

    </div>
  );
}
