import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { CheckCircle2, Circle, Mail, Sparkles, Building2, Calendar, Loader2 } from 'lucide-react';
import { OnboardingClient } from '../../data/mockData';
import { api } from '../../services/api';

export const OnboardingView = () => {
  const [clients, setClients] = useState<OnboardingClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendingReminder, setSendingReminder] = useState<string | null>(null);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const data = await api.getOnboardingClients();
        setClients(data);
      } catch (error) {
        console.error("Failed to load onboarding clients", error);
      } finally {
        setLoading(false);
      }
    };
    fetchClients();
  }, []);

  const toggleStep = async (clientId: string, stepId: string) => {
    // Optimistic UI update
    let newStatus = false;
    setClients(clients.map(client => {
      if (client.id === clientId) {
        const newPasos = client.pasos.map(p => {
          if (p.id === stepId) {
            newStatus = !p.completed;
            return { ...p, completed: newStatus };
          }
          return p;
        });
        const completedCount = newPasos.filter(p => p.completed).length;
        const newProgreso = Math.round((completedCount / newPasos.length) * 100);
        return { ...client, pasos: newPasos, progreso: newProgreso };
      }
      return client;
    }));

    // API call
    try {
      await api.toggleOnboardingStep(clientId, stepId, newStatus);
    } catch (error) {
      console.error("Failed to toggle step on server", error);
      // Ideally revert state here on error
    }
  };

  const sendMagicReminder = async (clientId: string) => {
    setSendingReminder(clientId);
    try {
      await api.sendMagicReminder(clientId);
    } catch (error) {
      console.error("Failed to send magic reminder", error);
    } finally {
      setSendingReminder(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-10 h-10 text-ctx-teal animate-spin" />
      </div>
    );
  }

  const globalProgress = Math.round(clients.reduce((acc, curr) => acc + curr.progreso, 0) / (clients.length || 1));

  return (
    <div className="p-6 lg:p-10 max-w-[1200px] mx-auto w-full">
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Onboarding Activos</h1>
          <p className="text-gray-400 text-sm">Integra a tus nuevos clientes sin fricciones</p>
        </div>
        <div className="glass-card px-6 py-3 flex flex-col items-center border-ctx-teal/20 min-w-[200px]">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest font-rajdhani mb-1">Progreso Global de Integración</span>
          <div className="flex items-center gap-3 w-full">
            <div className="flex-1 h-2 bg-navy-dark rounded-full overflow-hidden border border-white/5">
              <div className="h-full bg-ctx-teal transition-all duration-500" style={{ width: `${globalProgress}%` }} />
            </div>
            <span className="text-lg font-orbitron font-bold text-white">{globalProgress}%</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {clients.map(client => (
          <motion.div key={client.id} layoutId={client.id}
            className="glass-card p-6 flex flex-col relative overflow-hidden group border-white/10 hover:border-ctx-teal/30 transition-colors">
            
            {sendingReminder === client.id && (
              <div className="absolute inset-0 bg-navy-dark/90 backdrop-blur-md z-10 flex flex-col items-center justify-center rounded-2xl border border-ctx-teal/40">
                <Loader2 className="w-8 h-8 text-ctx-teal animate-spin mb-3" />
                <span className="text-sm text-ctx-teal font-rajdhani uppercase tracking-widest font-bold text-center px-4">
                  Redactando y Enviando<br/>Recordatorio Mágico...
                </span>
              </div>
            )}

            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-1">
                  <Building2 className="w-4 h-4 text-ctx-teal" /> {client.empresa}
                </h3>
                <span className="text-xs text-gray-400 font-rajdhani uppercase tracking-widest bg-white/5 px-2 py-1 rounded-md">
                  Plan {client.plan}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-gray-500 block mb-1">PROGRESO</span>
                <span className="text-xl font-orbitron font-bold text-ctx-teal">{client.progreso}%</span>
              </div>
            </div>

            <div className="w-full h-1.5 bg-black/40 rounded-full mb-6 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-ctx-teal to-violet-500 transition-all duration-500" style={{ width: `${client.progreso}%` }} />
            </div>

            <div className="flex-1 flex flex-col gap-3 mb-6">
              {client.pasos.map((paso, idx) => (
                <button key={paso.id} onClick={() => toggleStep(client.id, paso.id)}
                  className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${paso.completed ? 'bg-ctx-teal/10 border-ctx-teal/30 text-white' : 'bg-black/20 border-white/5 text-gray-400 hover:bg-white/5'}`}>
                  {paso.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-ctx-teal flex-shrink-0" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-500 flex-shrink-0" />
                  )}
                  <div className="flex flex-col items-start text-left">
                    <span className="text-[10px] font-rajdhani uppercase tracking-widest opacity-70">Paso {idx + 1}</span>
                    <span className="text-sm font-semibold">{paso.label}</span>
                  </div>
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/5 mt-auto">
              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <Calendar className="w-3.5 h-3.5" />
                <span>Inició: {client.fecha_inicio}</span>
              </div>
              
              {client.progreso < 100 ? (
                <button onClick={() => sendMagicReminder(client.id)}
                  className="flex items-center gap-1.5 bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 border border-violet-500/30 px-3 py-1.5 rounded-lg transition-colors text-xs font-bold uppercase font-rajdhani tracking-widest">
                  <Sparkles className="w-3 h-3" /> Push AI
                </button>
              ) : (
                <button className="flex items-center gap-1.5 bg-ctx-teal/20 text-ctx-teal border border-ctx-teal/30 px-3 py-1.5 rounded-lg text-xs font-bold uppercase font-rajdhani tracking-widest cursor-default">
                  <CheckCircle2 className="w-3 h-3" /> Completado
                </button>
              )}
            </div>

          </motion.div>
        ))}
      </div>
    </div>
  );
};
