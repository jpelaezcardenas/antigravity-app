import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  LayoutDashboard, Wallet, ShieldCheck, Radar, Receipt,
  MessageSquare, Settings, TrendingUp, AlertTriangle,
  ArrowUpRight, ArrowDownRight, ChevronRight, Bell,
  Search, LogOut, Globe, Zap, Target, Menu, X,
  PieChart
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { MOCK_USER, MOCK_PULSO, formatCOP, formatCOPShort } from './data/mockData';
import { PulsoDiarioView } from './components/pulso/PulsoDiarioView';
import { CentinelaView } from './components/centinela/CentinelaView';
import { CobroView } from './components/cobro/CobroView';
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
  { id: 'cobro', label: 'Cobro Inteligente', icon: Receipt },
  { id: 'taty', label: 'Taty', icon: MessageSquare },
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

const SidebarContent = ({ activeTab, setActiveTab, onLogout, onClose }: any) => (
  <>
    <div className="flex items-center justify-between mb-10 px-2">
      <div className="flex flex-col gap-1">
        <span className="font-orbitron font-bold text-2xl leading-none tracking-tighter text-white">CONTEXIA</span>
        <span className="font-rajdhani text-[10px] text-ctx-teal tracking-[0.2em] uppercase font-bold">GPS for Cash Flow</span>
      </div>
      {onClose && <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg lg:hidden"><X className="w-5 h-5 text-gray-400" /></button>}
    </div>
    <nav className="space-y-1 flex-1">
      {navItems.map((item) => (
        <button key={item.id}
          onClick={() => { setActiveTab(item.id); onClose?.(); }}
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
        </button>
      ))}
    </nav>
    <button onClick={onLogout}
      className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:text-red-400 transition-colors mt-auto group">
      <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
      <span className="text-sm font-rajdhani uppercase tracking-widest font-bold">Cerrar Sesión</span>
    </button>
  </>
);

const DashboardHome = ({ setActiveTab }: { setActiveTab: (t: string) => void }) => (
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
                  <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorEgr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
              <YAxis stroke="rgba(255,255,255,0.3)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
              <Area type="monotone" dataKey="ingresos" stroke="#2DD4BF" fillOpacity={1} fill="url(#colorIng)" />
              <Area type="monotone" dataKey="egresos" stroke="#8B5CF6" fillOpacity={1} fill="url(#colorEgr)" />
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
                { label: 'Cobrar Facturas Vencidas', tab: 'cobro' },
                { label: 'Hablar con Taty', tab: 'taty' },
              ].map(a => (
                <button key={a.tab} onClick={() => setActiveTab(a.tab)}
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
            <AlertItem type="danger" title="Desviación de Gastos" desc="Gastos operativos exceden presupuesto por 15%" />
            <AlertItem type="warning" title="Vencimiento IVA" desc="Plazo límite en 3 días hábiles" />
            <AlertItem type="info" title="Nueva Oportunidad" desc="Optimización detectada en pagos a proveedores" />
          </div>
        </div>
        <div className="glass-card p-6 border-ctx-teal/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10"><Globe className="w-20 h-20" /></div>
          <h3 className="font-orbitron text-lg mb-2">Contexia Global</h3>
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

// --- Login View ---

const LoginView = ({ onLogin }: { onLogin: () => void }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => { setLoading(false); onLogin(); }, 800);
  };

  return (
    <div className="min-h-screen bg-navy-dark flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-ctx-teal/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-ctx-violet/10 blur-[120px] rounded-full" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-md w-full relative z-10">
        <div className="text-center mb-10">
          <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="flex flex-col items-center justify-center gap-1 mb-6">
            <span className="font-orbitron font-bold text-4xl leading-none tracking-tighter text-white">CONTEXIA</span>
            <span className="font-rajdhani text-xs text-ctx-teal tracking-[0.3em] uppercase font-semibold">GPS for Cash Flow & Tax Risk</span>
          </motion.div>
          <h2 className="text-xl text-gray-400 font-rajdhani uppercase tracking-widest">Portal Empresarial Premium</h2>
        </div>
        <div className="glass-card p-8 border-white/10">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs font-rajdhani uppercase tracking-widest text-gray-400 mb-2">Email Corporativo</label>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                  placeholder="usuario@empresa.com" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-rajdhani uppercase tracking-widest text-gray-400 mb-2">Contraseña</label>
              <div className="relative">
                <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                  placeholder="••••••••" />
              </div>
            </div>
            <div className="bg-ctx-teal/5 border border-ctx-teal/20 rounded-lg p-3">
              <p className="text-ctx-teal text-xs text-center">🔓 Modo demo: cualquier credencial funciona</p>
            </div>
            <button type="submit" disabled={loading} className="premium-button w-full flex items-center justify-center gap-2 py-4">
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><span>Ingresar al Dashboard</span><ChevronRight className="w-4 h-4" /></>}
            </button>
          </form>
          <div className="mt-8 pt-6 border-t border-white/5 text-center">
            <p className="text-xs text-gray-500 font-rajdhani uppercase tracking-widest">
              ¿No tienes cuenta? <a href="/landing.html#contact" className="text-ctx-teal hover:underline">Solicitar Acceso Premium</a>
            </p>
          </div>
        </div>
        <p className="mt-8 text-center text-[10px] text-gray-600 font-rajdhani uppercase tracking-[0.2em]">Powered by Contexia AI Engine • v2.0.4</p>
      </motion.div>
    </div>
  );
};

// --- Main App ---

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('inicio');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('cx_user');
    if (saved) setUser(JSON.parse(saved));
    setLoading(false);
  }, []);

  const handleLogin = () => {
    localStorage.setItem('cx_user', JSON.stringify(MOCK_USER));
    localStorage.setItem('token', MOCK_USER.token);
    setUser(MOCK_USER);
  };

  const handleLogout = () => {
    localStorage.removeItem('cx_user');
    localStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-dark flex items-center justify-center">
        <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="text-center">
          <div className="w-16 h-16 border-4 border-ctx-teal border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-orbitron text-ctx-teal tracking-widest uppercase text-sm">Cargando Contexia...</p>
        </motion.div>
      </div>
    );
  }

  if (!user) return <LoginView onLogin={handleLogin} />;

  const tabTitles: Record<string, string> = {
    inicio: 'Panel de Control',
    pulso: '📊 Pulso Diario',
    centinela: '🛡️ Centinela Fiscal',
    cobro: '💰 Cobro Inteligente',
    taty: '💚 Taty — Tu Amiga Contadora',
    auditoria: '🔍 Auditoría Sombra',
    radar: '📡 Radar Predictivo',
    configuracion: '⚙️ Configuración',
  };

  const renderTab = () => {
    switch (activeTab) {
      case 'inicio': return <DashboardHome setActiveTab={setActiveTab} />;
      case 'pulso': return <PulsoDiarioView />;
      case 'centinela': return <CentinelaView />;
      case 'cobro': return <CobroView />;
      case 'taty': return <TatyView />;
      case 'auditoria': return (
        <ComingSoonView icon="auditoria" titulo="Auditoría Sombra"
          subtitulo="¿Qué sabe la DIAN de ti que tú no sabes?"
          descripcion="Cruzaremos los datos que la DIAN ya tiene de tus pasarelas (Stripe, MercadoPago, Nequi) con tu contabilidad para detectar inconsistencias antes de que te sorprendan."
          features={['Cruce automático', 'Detección de discrepancias', 'Alertas preventivas', 'Reporte detallado']} />
      );
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
        <SidebarContent activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} />
      </aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden" onClick={() => setMobileMenuOpen(false)} />
            <motion.aside initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }} transition={{ type: 'spring', damping: 25 }}
              className="fixed left-0 top-0 h-screen w-72 bg-navy-light/95 backdrop-blur-xl border-r border-white/5 flex flex-col p-6 z-50 lg:hidden">
              <SidebarContent activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} onClose={() => setMobileMenuOpen(false)} />
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
            <div className="flex items-center gap-2">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-bold text-white">{MOCK_USER.nombre_empresa}</p>
                <p className="text-[10px] text-ctx-teal uppercase tracking-widest font-bold">Empresario</p>
              </div>
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-ctx-teal to-ctx-violet p-[2px]">
                <div className="w-full h-full bg-navy-dark rounded-[10px] flex items-center justify-center font-bold text-ctx-teal text-sm">
                  {MOCK_USER.nombre_empresa.charAt(0)}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 custom-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div key={activeTab} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h1 className="text-2xl md:text-3xl font-orbitron font-bold text-white mb-1">{tabTitles[activeTab]}</h1>
                  <p className="text-gray-400 text-sm">Bienvenido, <span className="text-ctx-teal font-semibold">{MOCK_USER.nombre_empresa}</span></p>
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
