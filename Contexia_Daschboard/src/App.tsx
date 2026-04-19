/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import {
  LayoutDashboard,
  Wallet,
  ShieldCheck,
  Radar,
  ListChecks,
  MessageSquare,
  MessageCircle,
  Settings,
  Search,
  Bell,
  UserCircle,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  ShieldAlert,
  BrainCircuit,
  LogOut,
} from 'lucide-react';
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

export default function App() {
  const [user, setUser] = React.useState<any>(null);

  React.useEffect(() => {
    const session = localStorage.getItem('cx_session');
    if (session) {
      setUser(JSON.parse(session));
    } else {
      window.location.href = 'login.html';
    }
  }, []);

  return (
    <div className="min-h-screen bg-ctx-bg text-ctx-muted flex font-sans selection:bg-ctx-teal/30">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNav user={user} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <DashboardContent user={user} />
        </main>
      </div>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="w-64 border-r border-ctx-border bg-ctx-surface flex-col hidden lg:flex">
      <div className="h-16 flex items-center px-6 border-b border-ctx-border">
        <div className="flex items-center gap-3 text-ctx-text">
          <ContexiaLogo className="w-10 h-10 shrink-0" />
          <div className="flex flex-col">
            <span className="font-orbitron font-bold text-xl leading-none tracking-tight text-white mb-[2px]">CONTEXIA</span>
            <span className="font-rajdhani text-[9px] text-ctx-teal tracking-[0.2em] uppercase font-semibold">GPS for Cash Flow & Tax Risk</span>
          </div>
        </div>
      </div>
      <div className="p-4">
        <div className="text-xs font-semibold text-ctx-muted uppercase tracking-widest mb-4 mt-2">
          Módulos
        </div>
        <nav className="space-y-1">
          <NavItem icon={LayoutDashboard} label="Inicio" active />
          <NavItem icon={Wallet} label="Flujo de Caja" />
          <NavItem icon={ShieldCheck} label="Centinela Fiscal" />
          <NavItem icon={Radar} label="Radar Predictivo" />
          <NavItem icon={ListChecks} label="Conciliación" />
          <NavItem icon={MessageSquare} label="Copiloto" />
          <NavItem icon={Settings} label="Configuración" />
        </nav>
      </div>
      <div className="mt-auto p-4">
        <div className="glass-card bg-gradient-to-br from-ctx-surface/50 to-ctx-bg/50 border border-ctx-border p-4 rounded-2xl flex flex-col gap-3">
          <div className="text-sm font-semibold text-ctx-text flex items-center justify-between">
            Plan Premium
          </div>
          <div className="h-1.5 w-full bg-ctx-bg rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-ctx-teal to-ctx-violet w-3/4 rounded-full" />
          </div>
          <div className="text-xs text-ctx-muted font-medium">14 días restantes de prueba</div>
        </div>

        <button 
          onClick={() => {
            localStorage.removeItem('cx_session');
            window.location.href = 'login.html';
          }}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-ctx-muted hover:text-red-400 hover:bg-red-400/10 transition-colors mt-2 w-full"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm font-medium">Cerrar Sesión</span>
        </button>
      </div>
    </aside>
  );
}

function NavItem({
  icon: Icon,
  label,
  active,
  badge,
}: {
  icon: any;
  label: string;
  active?: boolean;
  badge?: string;
}) {
  return (
    <a
      href="#"
      className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition-all duration-300 ${
        active
          ? 'bg-ctx-teal/10 text-ctx-teal font-semibold border border-ctx-teal/20 shadow-[0_0_15px_-5px_rgba(45,212,191,0.3)]'
          : 'text-ctx-muted hover:text-ctx-text hover:bg-ctx-surface/50'
      }`}
    >
      <div className="flex items-center gap-3">
        <Icon className={`w-5 h-5 transition-colors ${active ? 'text-ctx-teal' : 'text-ctx-muted'}`} />
        <span className="text-sm font-rajdhani tracking-wide">{label}</span>
      </div>
      {badge && (
        <span className="px-2 py-0.5 rounded-md bg-ctx-violet/10 text-ctx-violet text-[10px] font-bold tracking-wider border border-ctx-violet/20 uppercase font-orbitron">
          {badge}
        </span>
      )}
    </a>
  );
}

function TopNav({ user }: { user: any }) {
  const initials = user?.name ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().substring(0, 2) : 'UX';
  return (
    <header className="h-16 flex items-center justify-between px-4 lg:px-8 border-b border-ctx-border bg-ctx-bg/80 backdrop-blur-md sticky top-0 z-10">
      <div className="flex items-center gap-4 lg:hidden">
        <BrainCircuit className="w-6 h-6 text-ctx-teal" />
      </div>

      <div className="hidden lg:block relative w-96">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ctx-muted" />
        <input
          type="text"
          placeholder="Buscar transacciones, facturas..."
          className="w-full bg-ctx-panel border border-ctx-border rounded-xl pl-10 pr-4 py-2 text-sm text-ctx-text placeholder:text-ctx-muted focus:outline-none focus:border-ctx-muted focus:ring-1 focus:ring-ctx-muted transition-all"
        />
      </div>

      <div className="flex items-center gap-4 lg:gap-6">
        <div className="flex items-center gap-3">
          <button className="relative p-2 text-ctx-muted hover:text-ctx-text transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-ctx-yellow rounded-full border-2 border-ctx-bg"></span>
          </button>
          <button className="flex items-center gap-2 pl-2 group">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-ctx-teal to-ctx-violet p-[1px] group-hover:scale-110 transition-transform">
              <div className="w-full h-full rounded-full bg-ctx-panel border-2 border-ctx-bg flex items-center justify-center">
                <span className="text-xs font-bold text-white group-hover:text-ctx-teal transition-colors">{initials}</span>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-ctx-muted group-hover:text-ctx-text transition-colors" />
          </button>
        </div>
        
        {/* Logo superior derecho */}
        <div className="hidden lg:flex items-center gap-3 pl-6 border-l border-ctx-border relative">
            <ContexiaLogo className="w-10 h-10" />
            <div className="flex flex-col pt-1">
              <span className="font-orbitron font-bold text-[15px] leading-none tracking-tight text-white uppercase">CONTEXIA</span>
              <span className="font-rajdhani text-[8px] text-ctx-teal tracking-[0.2em] uppercase mt-[2px] font-bold">GPS For Cash Flow</span>
            </div>
        </div>
      </div>
    </header>
  );
}

function DashboardContent({ user }: { user: any }) {
  const firstName = user?.name ? user.name.split(' ')[0] : 'Usuario';
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 py-2">
        <div>
          <h1 className="text-3xl font-orbitron font-bold text-white tracking-tight">
            Hola, <span className="gradient-text">{firstName}</span> 👋
          </h1>
          <p className="text-sm text-ctx-muted mt-2 font-rajdhani font-semibold tracking-wide uppercase opacity-80">
            Aquí tienes el resumen de tu empresa al día de hoy.
          </p>
        </div>
        <div className="flex gap-3">
          <button className="px-5 py-2.5 bg-ctx-panel border border-ctx-border hover:bg-ctx-surface/80 text-ctx-text text-sm font-semibold rounded-xl transition-all hover:scale-105 active:scale-95 shadow-lg">
            Descargar Reporte
          </button>
          <button className="px-5 py-2.5 bg-gradient-to-r from-ctx-teal to-ctx-violet hover:brightness-110 text-ctx-panel text-sm font-bold rounded-xl shadow-[0_4px_20px_-4px_rgba(45,212,191,0.4)] transition-all hover:scale-105 active:scale-95">
            Nueva Transacción
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Caja Real Hoy"
          value="$2,500,000 COP"
          trend=""
          isUp={true}
          icon={Wallet}
          color="teal"
          highlight
        />
        <KpiCard
          title="Impuestos Estimados"
          value="$850,000 COP"
          trend=""
          isUp={false}
          icon={Radar}
          color="violet"
        />
        <KpiCard
          title="Riesgo Fiscal"
          value="Bajo"
          trend=""
          isUp={true}
          icon={ShieldAlert}
          color="teal"
          highlight
        />
        <KpiCard
          title="Alertas Activas"
          value="3"
          trend=""
          isUp={false}
          icon={AlertTriangle}
          color="yellow"
          highlight
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Main Chart */}
        <div className="lg:col-span-3 space-y-5">
          <Card>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-orbitron font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-ctx-teal" />
                  GPS de Flujo de Caja
                </h2>
                <p className="text-sm text-ctx-muted">
                  Ingresos vs Egresos de los últimos 30 días
                </p>
              </div>
              <select className="bg-ctx-bg border border-ctx-border text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ctx-muted">
                <option>Últimos 30 días</option>
                <option>Proyección 30 días</option>
              </select>
            </div>
            <div className="h-80 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={data}
                  margin={{ top: 10, right: 0, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorIngresos" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorEgresos" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" vertical={false} />
                  <XAxis dataKey="name" stroke="#A0AEC0" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#A0AEC0" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val/1000}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1A1A1A', borderColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '12px' }}
                    itemStyle={{ color: '#FFFFFF' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="ingresos"
                    stroke="#2DD4BF"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorIngresos)"
                  />
                  <Area
                    type="monotone"
                    dataKey="egresos"
                    stroke="#8B5CF6"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorEgresos)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-orbitron font-bold text-white flex items-center gap-2">
                <ListChecks className="w-5 h-5 text-ctx-teal" />
                Conciliación Bancaria 4.0
              </h2>
              <button className="text-sm text-ctx-teal hover:text-ctx-violet font-bold transition-colors font-rajdhani uppercase tracking-widest">
                Ver detalle
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-ctx-muted">Progreso mensual</span>
                <span className="text-ctx-text font-medium">85% completado</span>
              </div>
              <div className="h-2 w-full bg-ctx-bg rounded-full overflow-hidden border border-ctx-border">
                <div className="h-full bg-gradient-to-r from-ctx-teal to-ctx-violet w-[85%] rounded-full relative shadow-[0_0_10px_rgba(45,212,191,0.5)]">
                  <div className="absolute inset-0 bg-white/10 blur-[1px] mix-blend-overlay"></div>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-ctx-border">
                 <div className="text-center p-2 rounded-xl bg-ctx-bg/30">
                    <div className="text-2xl font-semibold text-ctx-text">124</div>
                    <div className="text-xs text-ctx-muted mt-1">Cruzados</div>
                 </div>
                 <div className="text-center p-2 rounded-xl bg-ctx-yellow/10 border border-ctx-yellow/20">
                    <div className="text-2xl font-semibold text-ctx-yellow">12</div>
                    <div className="text-xs text-ctx-muted mt-1">Pendientes</div>
                 </div>
                 <div className="text-center p-2 rounded-xl bg-ctx-bg/30">
                    <div className="text-2xl font-semibold text-ctx-text">4</div>
                    <div className="text-xs text-ctx-muted mt-1">Cuentas</div>
                 </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Sidebar */}
        <div className="lg:col-span-1 space-y-5">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-orbitron font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-ctx-orange" />
                Centinela Fiscal
              </h2>
            </div>
            <div className="space-y-3">
              {[
                { risk: 'alto', text: 'Gasto sin soporte DIAN válido', amount: '$450.000', id: 'TX-892' },
                { risk: 'medio', text: 'Diferencia en retención', amount: '$12.500', id: 'TX-721' },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-xl bg-ctx-bg border border-ctx-border hover:border-ctx-muted transition-colors cursor-pointer group">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${item.risk === 'alto' ? 'bg-ctx-orange' : 'bg-ctx-violet'} animate-pulse`} />
                      <span className="text-xs font-bold text-ctx-text font-orbitron">{item.id}</span>
                    </div>
                    <span className="text-xs font-mono text-ctx-muted">{item.amount}</span>
                  </div>
                  <p className="text-sm text-ctx-text font-medium leading-snug">{item.text}</p>
                  <div className="mt-3 flex items-center text-xs text-ctx-muted font-medium group-hover:text-ctx-blue transition-colors">
                    Revisar ahora <ArrowRight className="w-3 h-3 ml-1" />
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-4 py-2 text-sm text-ctx-muted hover:text-ctx-text border border-ctx-border hover:bg-ctx-surface rounded-lg transition-colors">
              Ver todas (4)
            </button>
          </Card>

          <Card>
            <div className="bg-gradient-to-br from-ctx-panel to-ctx-surface -m-6 p-6 space-y-4 rounded-2xl border border-ctx-blue/20 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-ctx-blue/10 blur-xl rounded-full translate-x-10 -translate-y-10" />
              
              <div className="relative z-10">
                <h2 className="text-xl font-orbitron font-bold text-white flex items-center gap-2 mb-1">
                  <Radar className="w-5 h-5 text-ctx-teal" />
                  Radar Predictivo
                </h2>
                <p className="text-sm text-ctx-muted mb-4">
                  Próximo pago estimado de ICA y Retefuente.
                </p>
                
                <div className="text-3xl font-light text-ctx-text mb-1">
                  $18.4 <span className="text-xl text-ctx-text/50">Millones</span>
                </div>
                
                <div className="flex items-center justify-between text-sm mt-4">
                  <span className="text-ctx-muted">Fecha límite:</span>
                  <span className="text-ctx-text font-medium">12 Oct 2024</span>
                </div>
              </div>
            </div>
          </Card>
          
          <div className="bg-ctx-bg border border-ctx-cyan/30 rounded-2xl p-5 flex flex-col relative overflow-hidden">
             <div className="absolute top-0 right-0 w-32 h-32 bg-ctx-cyan/10 blur-xl rounded-full translate-x-10 -translate-y-10" />
            <div className="flex items-center gap-2 mb-4 relative z-10">
              <span className="font-orbitron font-bold text-white text-lg">Copiloto Fiscal</span>
            </div>
            
            <button className="bg-ctx-panel border border-ctx-border rounded-xl p-3 flex items-center gap-3 hover:bg-ctx-surface transition-colors relative z-10 w-full mb-6 text-left group">
               <div className="w-10 h-10 rounded-full bg-[#25D366] flex items-center justify-center shrink-0 shadow-md">
                  <MessageCircle className="w-5 h-5 text-white" />
               </div>
               <div>
                  <div className="text-xs text-ctx-muted font-medium mb-0.5">Acceso Rápido</div>
                  <div className="text-sm font-semibold text-ctx-text group-hover:text-ctx-lime transition-colors">Chat con Experto</div>
               </div>
            </button>

            <div className="relative z-10">
               <h4 className="text-[13px] text-ctx-muted mb-3 font-medium">Accesos FAQs rápido:</h4>
               <ul className="space-y-2.5 text-[13px] text-ctx-muted/80">
                  <li className="flex items-start gap-2 before:content-['•'] before:text-ctx-text">
                     Chat con un asesor experto?
                  </li>
                  <li className="flex items-start gap-2 before:content-['•'] before:text-ctx-text">
                     Chat con un cargo de despido?
                  </li>
                  <li className="flex items-start gap-2 before:content-['•'] before:text-ctx-text">
                     Chat con un equipo de FAQs?
                  </li>
               </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`glass-card rounded-2xl p-6 overflow-hidden hover:border-ctx-teal/30 transition-all duration-300 group ${className}`}
    >
      {children}
    </div>
  );
}

function KpiCard({
  title,
  value,
  trend,
  isUp,
  icon: Icon,
  color,
  highlight = false,
  trendLabel
}: {
  title: string;
  value: string;
  trend: string;
  isUp: boolean;
  icon: any;
  color: 'teal' | 'violet' | 'yellow' | 'red';
  highlight?: boolean;
  trendLabel?: string;
}) {
  const bgColors = {
    teal: 'bg-ctx-teal/10 border-ctx-teal/20',
    violet: 'bg-ctx-violet/10 border-ctx-violet/20',
    yellow: 'bg-ctx-yellow/10 border-ctx-yellow/20',
    red: 'bg-ctx-orange/10 border-ctx-orange/20',
  };

  const textColors = {
    teal: 'text-ctx-teal',
    violet: 'text-ctx-violet',
    yellow: 'text-ctx-yellow',
    red: 'text-ctx-orange',
  };

  const trendColor = isUp ? 'text-ctx-teal' : 'text-ctx-muted';

  return (
    <div
      className={`relative glass-card rounded-xl p-5 hover:scale-105 transition-all duration-300 group ${
        highlight 
        ? color === 'red' ? 'border-ctx-orange/50 shadow-[0_0_20px_rgba(249,115,22,0.15)]' 
          : color === 'teal' ? 'border-ctx-teal/40 shadow-[0_0_20px_rgba(45,212,191,0.15)]'
          : color === 'yellow' ? 'border-ctx-yellow/40 shadow-[0_0_20px_rgba(251,191,36,0.15)]'
          : 'border-ctx-violet/40 shadow-[0_0_20px_rgba(139,92,246,0.15)]'
        : 'border-ctx-border'
      }`}
    >
       {highlight && (
         <div className={`absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-${color === 'red' ? 'ctx-orange' : color === 'teal' ? 'ctx-teal' : color === 'yellow' ? 'ctx-yellow' : 'ctx-violet'} to-transparent opacity-50`} />
       )}
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-[12px] font-rajdhani font-bold uppercase tracking-wider text-ctx-muted group-hover:text-ctx-text transition-colors">{title}</h3>
        {value === 'Bajo' || value === 'Medio' || value === 'Alto' ? (
           <div className={`px-3 py-1 rounded-full border text-xs font-semibold ${bgColors[color]}`}>
             {value}
           </div>
        ) : (
          <div className={`p-2 rounded-lg border hidden`}>
            <Icon className={`w-4 h-4 ${textColors[color]}`} />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl lg:text-[28px] font-orbitron font-bold leading-none tracking-tight ${
           value === 'Bajo' || value === 'Medio' || value === 'Alto' ? textColors[color] : 'text-white'
        }`}>{value !== 'Bajo' && value !== 'Medio' && value !== 'Alto' ? value : ''}</span>
      </div>
      {trend && (
      <div className="mt-2 flex items-center text-xs">
        {trendLabel ? (
            <span className="text-ctx-muted mr-1">{trendLabel}:</span>
        ) : (
          isUp ? <TrendingUp className="w-3 h-3 mr-1 text-ctx-teal" /> : <TrendingDown className="w-3 h-3 mr-1 text-ctx-muted" />
        )}
        <span className={`font-rajdhani font-bold uppercase tracking-widest ${trendLabel ? textColors[color] : trendColor}`}>{trend}</span>
      </div>
      )}
    </div>
  );
}

export function ContexiaShield({ className = "w-8 h-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="shield-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FBBF24" />
          <stop offset="50%" stopColor="#2DD4BF" />
          <stop offset="100%" stopColor="#8B5CF6" />
        </linearGradient>
      </defs>
      <path d="M16 3 L4 8 V15 C4 22 9 27 16 30 C23 27 28 22 28 15 V8 L16 3 Z" stroke="url(#shield-grad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function ContexiaLogo({ className = "w-10 h-10" }: { className?: string }) {
  return (
    <svg viewBox="0 0 120 140" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="pin-left" x1="0%" y1="100%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="#8B5CF6"/>
          <stop offset="50%" stopColor="#2DD4BF"/>
          <stop offset="100%" stopColor="#2DD4BF"/>
        </linearGradient>
        <linearGradient id="pin-right" x1="0%" y1="0%" x2="0%" y2="100%">
           <stop offset="0%" stopColor="#2DD4BF"/>
           <stop offset="50%" stopColor="#8B5CF6"/>
           <stop offset="100%" stopColor="#1E293B"/>
        </linearGradient>
        <linearGradient id="bar-green" x1="0%" y1="0%" x2="0%" y2="100%">
           <stop offset="0%" stopColor="#2DD4BF"/>
           <stop offset="100%" stopColor="#134E4A"/>
        </linearGradient>
        <linearGradient id="bar-yellow" x1="0%" y1="0%" x2="0%" y2="100%">
           <stop offset="0%" stopColor="#FBBF24"/>
           <stop offset="100%" stopColor="#92400E"/>
        </linearGradient>
        <linearGradient id="bar-cyan" x1="0%" y1="0%" x2="0%" y2="100%">
           <stop offset="0%" stopColor="#8B5CF6"/>
           <stop offset="100%" stopColor="#4C1D95"/>
        </linearGradient>
        <linearGradient id="orbit" x1="0%" y1="0%" x2="100%" y2="0%">
           <stop offset="0%" stopColor="#2DD4BF"/>
           <stop offset="100%" stopColor="#8B5CF6"/>
        </linearGradient>
        <linearGradient id="pin-bottom" x1="0%" y1="0%" x2="100%" y2="0%">
           <stop offset="0%" stopColor="#2DD4BF"/>
           <stop offset="100%" stopColor="#8B5CF6"/>
        </linearGradient>
      </defs>

      <path d="M 60 130 C 40 100, 20 75, 20 50 A 40 40 0 0 1 60 10" stroke="url(#pin-left)" strokeWidth="6" strokeLinecap="round" />
      <path d="M 60 10 A 40 40 0 0 1 100 50 C 100 75, 80 100, 60 130" stroke="url(#pin-right)" strokeWidth="6" strokeLinecap="round" />
      
      <path d="M 50 110 L 60 130 L 70 110 Q 60 120 50 110 Z" fill="url(#pin-bottom)" />
      
      <rect x="35" y="60" width="12" height="25" rx="3" fill="url(#bar-green)"/>
      <rect x="54" y="42" width="12" height="43" rx="3" fill="url(#bar-yellow)"/>
      <rect x="73" y="25" width="12" height="60" rx="3" fill="url(#bar-cyan)"/>

      <circle cx="60" cy="27" r="7" fill="#EEEEEE" />

      <path d="M 12 85 Q 60 125 105 45" stroke="url(#orbit)" strokeWidth="4" strokeLinecap="round" fill="none"/>
      
      <path d="M 94 40 L 115 35 L 105 58 Z" fill="#8B5CF6"/>

      <circle cx="20" cy="80" r="3" fill="#2DD4BF"/>
      <circle cx="55" cy="105" r="4.5" fill="#121212" stroke="#FFFFFF" strokeWidth="2.5"/>
      <circle cx="70" cy="102" r="4.5" fill="#121212" stroke="#FFFFFF" strokeWidth="2.5"/>
    </svg>
  );
}

