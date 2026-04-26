/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { supabase } from './lib/supabase';
import { usePulso } from './hooks/usePulso';

import { 
  LayoutDashboard, 
  Wallet, 
  ShieldCheck, 
  Radar, 
  ListChecks, 
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Search,
  Bell,
  Settings,
  LogOut,
  ChevronRight,
  ExternalLink,
  Zap,
  Globe,
  PieChart,
  Target
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const data = [
  { name: '1', ingresos: 4000, egresos: 2400 },
  { name: '5', ingresos: 3000, egresos: 1398 },
  { name: '10', ingresos: 2000, egresos: 8000 },
  { name: '15', ingresos: 2780, egresos: 3908 },
  { name: '20', ingresos: 6890, egresos: 4800 },
  { name: '25', ingresos: 5390, egresos: 3800 },
  { name: '30', ingresos: 8490, egresos: 4300 },
];

// --- Sub-components ---

const StatCard = ({ icon: Icon, label, value, change, positive }: any) => (
  <motion.div 
    whileHover={{ translateY: -5 }}
    className="glass-card p-6 border-white/5 hover:border-ctx-teal/20 transition-all group"
  >
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
  const colors = {
    danger: 'text-red-400 border-red-500/20 bg-red-500/5',
    warning: 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5',
    info: 'text-blue-400 border-blue-500/20 bg-blue-500/5'
  };
  return (
    <div className={`p-3 rounded-xl border ${colors[type as keyof typeof colors] || colors.info}`}>
      <h4 className="text-sm font-bold mb-1">{title}</h4>
      <p className="text-xs text-gray-400">{desc}</p>
    </div>
  );
};

const Sidebar = ({ onLogout, activeTab, setActiveTab }: any) => {
  const items = [
    { id: 'inicio', label: 'Inicio', icon: LayoutDashboard },
    { id: 'flujo', label: 'Flujo de Caja', icon: Wallet },
    { id: 'centinela', label: 'Centinela Fiscal', icon: ShieldCheck },
    { id: 'radar', label: 'Radar Predictivo', icon: Radar },
    { id: 'conciliacion', label: 'Conciliación', icon: ListChecks },
    { id: 'copiloto', label: 'Copiloto AI', icon: MessageSquare },
  ];

  return (
    <aside className="w-72 bg-navy-light/50 backdrop-blur-xl border-r border-white/5 flex flex-col p-6">
      <div className="flex flex-col gap-1 mb-10 px-2">
        <span className="font-orbitron font-bold text-2xl leading-none tracking-tighter text-white">CONTEXIA</span>
        <span className="font-rajdhani text-[10px] text-ctx-teal tracking-[0.2em] uppercase font-bold">GPS for Cash Flow</span>
      </div>
      
      <nav className="space-y-2 flex-1">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all relative group ${
              activeTab === item.id 
                ? 'bg-ctx-teal/10 text-ctx-teal border border-ctx-teal/20' 
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
            }`}
          >
            {activeTab === item.id && (
              <motion.div 
                layoutId="activeNav"
                className="absolute left-[-24px] w-1 h-8 bg-ctx-teal rounded-r-full shadow-[0_0_15px_rgba(45,212,191,0.5)]" 
              />
            )}
            <item.icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${activeTab === item.id ? 'text-ctx-teal' : 'text-gray-500'}`} />
            <span className="font-rajdhani text-sm uppercase tracking-widest font-semibold">{item.label}</span>
          </button>
        ))}
      </nav>

      <button 
        onClick={onLogout}
        className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:text-red-400 transition-colors mt-auto group"
      >
        <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
        <span className="text-sm font-rajdhani uppercase tracking-widest font-bold">Cerrar Sesión</span>
      </button>
    </aside>
  );
};

const TopNav = ({ user }: any) => (
  <header className="h-20 border-b border-white/5 flex items-center justify-between px-8 bg-navy-dark/50 backdrop-blur-md">
    <div className="relative w-96">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
      <input 
        type="text" 
        placeholder="Buscar transacciones o informes..."
        className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-ctx-teal/50"
      />
    </div>
    <div className="flex items-center gap-4">
      <div className="text-right">
        <p className="text-sm font-bold text-white">{user.name}</p>
        <p className="text-[10px] text-ctx-teal uppercase tracking-widest font-bold">{user.role}</p>
      </div>
      <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-ctx-teal to-ctx-violet p-[2px]">
        <div className="w-full h-full bg-navy-dark rounded-[10px] flex items-center justify-center font-bold text-ctx-teal">
          {user.name.charAt(0).toUpperCase()}
        </div>
      </div>
    </div>
  </header>
);

const LoginView = ({ onLogin, loading, error, setEmail, setPassword, email, password }: any) => (
  <div className="min-h-screen bg-navy-dark flex items-center justify-center p-4 relative overflow-hidden">
    <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-ctx-teal/10 blur-[120px] rounded-full" />
    <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-ctx-violet/10 blur-[120px] rounded-full" />

    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-md w-full relative z-10"
    >
      <div className="text-center mb-10">
        <motion.div 
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          className="flex flex-col items-center justify-center gap-1 mb-6"
        >
          <span className="font-orbitron font-bold text-4xl leading-none tracking-tighter text-white">CONTEXIA</span>
          <span className="font-rajdhani text-xs text-ctx-teal tracking-[0.3em] uppercase font-semibold">GPS for Cash Flow & Tax Risk</span>
        </motion.div>
        <h2 className="text-xl text-gray-400 font-rajdhani uppercase tracking-widest">Portal Empresarial Premium</h2>
      </div>

      <div className="glass-card p-8 border-white/10">
        <form onSubmit={onLogin} className="space-y-6">
          <div>
            <label className="block text-xs font-rajdhani uppercase tracking-widest text-gray-400 mb-2">Email Corporativo</label>
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                placeholder="usuario@empresa.com"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-rajdhani uppercase tracking-widest text-gray-400 mb-2">Contraseña</label>
            <div className="relative">
              <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg flex items-center gap-2"
            >
              <AlertTriangle className="w-4 h-4" />
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="premium-button w-full flex items-center justify-center gap-2 py-4"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>Ingresar al Dashboard</span>
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
        
        <div className="mt-8 pt-6 border-t border-white/5 text-center">
          <p className="text-xs text-gray-500 font-rajdhani uppercase tracking-widest">
            ¿No tienes cuenta? <a href="/landing.html#contact" className="text-ctx-teal hover:underline transition-all">Solicitar Acceso Premium</a>
          </p>
        </div>
      </div>
      
      <p className="mt-8 text-center text-[10px] text-gray-600 font-rajdhani uppercase tracking-[0.2em]">
        Powered by Contexia AI Engine • v2.0.4
      </p>
    </motion.div>
  </div>
);

// --- Main Application ---

export default function App() {
  const [session, setSession] = useState<any>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [activeTab, setActiveTab] = useState('inicio');
  const [transactions, setTransactions] = useState(data);
  const { pulso } = usePulso(session?.user?.id || null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) fetchProfile(session.user.id);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        fetchProfile(session.user.id);
        fetchTransactions();
      }
      else setUserProfile(null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const fetchProfile = async (userId: string) => {
    const { data, error } = await supabase
      .from('profiles')
      .select('*, companies(*)')
      .eq('id', userId)
      .single();
    
    if (!error) setUserProfile(data);
  };

  const fetchTransactions = async () => {
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .order('date', { ascending: true });
    
    if (!error && data && data.length > 0) {
      const mapped = data.map(t => ({
        name: new Date(t.date).getDate().toString(),
        ingresos: t.type === 'income' ? Number(t.amount) : 0,
        egresos: t.type === 'expense' ? Number(t.amount) : 0
      }));
      setTransactions(mapped);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    
    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) setAuthError(error.message);
    setAuthLoading(false);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-dark flex items-center justify-center">
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-ctx-teal border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="font-orbitron text-ctx-teal tracking-widest uppercase text-sm">Cargando Contexia...</p>
        </motion.div>
      </div>
    );
  }

  if (session && userProfile && userProfile.role !== 'Empresario' && userProfile.role !== 'Admin') {
    return (
      <div className="min-h-screen bg-navy-dark flex items-center justify-center p-6 text-center">
        <div className="glass-card max-w-md p-8 border-red-500/30">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="font-orbitron text-2xl mb-4">Acceso Denegado</h1>
          <p className="text-gray-400 mb-6">
            Esta versión del portal está reservada exclusivamente para el perfil <strong>Empresario</strong>.
          </p>
          <button 
            onClick={handleLogout}
            className="premium-button-secondary px-6 py-3"
          >
            Cerrar Sesión
          </button>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <LoginView 
        onLogin={handleLogin} 
        loading={authLoading} 
        error={authError}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
      />
    );
  }

  const user = {
    name: userProfile?.name || session.user.email?.split('@')[0],
    role: userProfile?.role || 'User',
    company: userProfile?.companies?.name || 'Empresa'
  };

  return (
    <div className="min-h-screen bg-navy-dark text-white flex font-sans selection:bg-ctx-teal/30">
      <Sidebar onLogout={handleLogout} activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNav user={user} />
        <main className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h1 className="text-3xl font-orbitron font-bold text-white mb-2">
                    {activeTab === 'inicio' ? 'Panel de Control' : 
                     activeTab === 'flujo' ? 'Flujo de Caja' :
                     activeTab === 'centinela' ? 'Centinela Fiscal' :
                     activeTab === 'radar' ? 'Radar Predictivo' :
                     activeTab === 'conciliacion' ? 'Conciliación Bancaria' : 'Copiloto AI'}
                  </h1>
                  <p className="text-gray-400">Bienvenido de nuevo, <span className="text-ctx-teal font-semibold">{user.name}</span></p>
                </div>
                
                <div className="flex items-center gap-4">
                  <div className="bg-white/5 border border-white/10 rounded-full px-4 py-2 flex items-center gap-2">
                    <div className="w-2 h-2 bg-ctx-teal rounded-full animate-pulse" />
                    <span className="text-xs font-rajdhani uppercase tracking-wider text-gray-300">Mercado: Abierto</span>
                  </div>
                  <button className="p-2 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors relative">
                    <Bell className="w-5 h-5 text-gray-400" />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-ctx-violet rounded-full" />
                  </button>
                </div>
              </div>

              {activeTab === 'inicio' ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <StatCard 
                      icon={TrendingUp} 
                      label="EBITDA Proyectado" 
                      value="$1.2M" 
                      change="+12.5%" 
                      positive={true} 
                    />
                    <StatCard 
                      icon={Wallet} 
                      label="Caja Disponible" 
                      value="$450k" 
                      change="-2.4%" 
                      positive={false} 
                    />
                    <StatCard 
                      icon={ShieldCheck} 
                      label="Riesgo Fiscal" 
                      value="4.2%" 
                      change="-0.5%" 
                      positive={true} 
                    />
                    <StatCard 
                      icon={Radar} 
                      label="Oportunidades" 
                      value="8" 
                      change="+3" 
                      positive={true} 
                    />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                    <div className="lg:col-span-2 space-y-8">
                      <div className="glass-card p-6 h-[400px] flex items-center justify-center border-ctx-teal/20 relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-br from-ctx-teal/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="text-center relative z-10">
                          <TrendingUp className="w-12 h-12 text-ctx-teal mx-auto mb-4 opacity-50" />
                          <p className="font-orbitron text-xl text-gray-300 mb-2">Gráfico de Flujo de Caja</p>
                          <p className="text-sm text-gray-500 font-rajdhani uppercase tracking-widest">Visualización en Tiempo Real</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="glass-card p-6 border-ctx-violet/20">
                          <h3 className="font-orbitron text-lg mb-4 flex items-center gap-2">
                            <Zap className="w-5 h-5 text-ctx-violet" />
                            Acciones Rápidas
                          </h3>
                          <div className="space-y-3">
                            <button className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors flex items-center justify-between group">
                              <span className="text-sm">Generar Informe Mensual</span>
                              <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-ctx-violet transition-colors" />
                            </button>
                            <button className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors flex items-center justify-between group">
                              <span className="text-sm">Conciliar Facturas Pendientes</span>
                              <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-ctx-violet transition-colors" />
                            </button>
                          </div>
                        </div>
                        <div className="glass-card p-6 border-ctx-teal/20">
                          <h3 className="font-orbitron text-lg mb-4 flex items-center gap-2">
                            <Target className="w-5 h-5 text-ctx-teal" />
                            Metas Financieras
                          </h3>
                          <div className="space-y-4">
                            <div>
                              <div className="flex justify-between text-xs mb-1 uppercase tracking-tighter text-gray-400">
                                <span>Reserva de Caja</span>
                                <span>85%</span>
                              </div>
                              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-ctx-teal w-[85%]" />
                              </div>
                            </div>
                            <div>
                              <div className="flex justify-between text-xs mb-1 uppercase tracking-tighter text-gray-400">
                                <span>Optimización Impuestos</span>
                                <span>62%</span>
                              </div>
                              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-ctx-violet w-[62%]" />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-8">
                      <div className="glass-card p-6 border-white/10 bg-navy-light/30">
                        <h3 className="font-orbitron text-lg mb-6">Alertas Críticas</h3>
                        <div className="space-y-4">
                          <AlertItem 
                            type="danger" 
                            title="Desviación de Gastos" 
                            desc="Gastos operativos exceden presupuesto por 15%" 
                          />
                          <AlertItem 
                            type="warning" 
                            title="Vencimiento IVA" 
                            desc="Plazo límite en 3 días hábiles" 
                          />
                          <AlertItem 
                            type="info" 
                            title="Nueva Oportunidad" 
                            desc="Optimización detectada en pagos a proveedores" 
                          />
                        </div>
                      </div>

                      <div className="glass-card p-6 border-ctx-teal/10 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                          <Globe className="w-20 h-20" />
                        </div>
                        <h3 className="font-orbitron text-lg mb-2">Contexia Global</h3>
                        <p className="text-sm text-gray-400 mb-4">Tu empresa está operando bajo estándares internacionales.</p>
                        <div className="flex gap-2">
                          <div className="px-2 py-1 bg-ctx-teal/10 text-ctx-teal text-[10px] rounded uppercase font-bold tracking-widest">NIIF</div>
                          <div className="px-2 py-1 bg-ctx-violet/10 text-ctx-violet text-[10px] rounded uppercase font-bold tracking-widest">DIAN</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="glass-card p-12 text-center border-dashed border-white/10 min-h-[600px] flex flex-col items-center justify-center">
                  <div className="w-20 h-20 rounded-full bg-ctx-teal/10 flex items-center justify-center mb-6">
                    <Radar className="w-10 h-10 text-ctx-teal animate-pulse" />
                  </div>
                  <h2 className="font-orbitron text-2xl mb-4">Módulo en Desarrollo</h2>
                  <p className="text-gray-400 max-w-md mx-auto mb-8">
                    Estamos calibrando los algoritmos de precisión para este módulo. Estará disponible en la próxima actualización premium.
                  </p>
                  <button className="premium-button px-8 py-3">Notificar cuando esté listo</button>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
