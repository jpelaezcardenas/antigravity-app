import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Target, Phone, FileText, CheckCircle2, ChevronRight, MoreHorizontal, Sparkles, Loader2, AlertTriangle } from 'lucide-react';
import { CRMLead, CRMLeadStatus, formatCOP } from '../../data/mockData';
import { api } from '../../services/api';

const COLUMNAS: { id: CRMLeadStatus; label: string; icon: React.FC<any>; color: string }[] = [
  { id: 'prospecto', label: 'Prospectos', icon: Target, color: 'text-blue-400' },
  { id: 'llamada', label: 'Llamada Agendada', icon: Phone, color: 'text-yellow-400' },
  { id: 'propuesta', label: 'Propuesta Enviada', icon: FileText, color: 'text-purple-400' },
  { id: 'ganado', label: 'Ganado / Cierre', icon: CheckCircle2, color: 'text-ctx-teal' },
];

export const CRMView = () => {
  const [leads, setLeads] = useState<CRMLead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeads = async () => {
      try {
        const data = await api.getCrmLeads();
        setLeads(data);
      } catch (error) {
        console.error("Failed to fetch CRM leads", error);
      } finally {
        setLoading(false);
      }
    };
    fetchLeads();
  }, []);

  const getLeadsByStatus = (status: CRMLeadStatus) => leads.filter(l => l.estado === status);

  const moveLead = async (id: string, newStatus: CRMLeadStatus) => {
    // Optimistic Update
    setLeads(leads.map(l => l.id === id ? { ...l, estado: newStatus } : l));
    try {
      await api.updateLeadStatus(id, newStatus);
    } catch (error) {
      console.error("Failed to move lead status", error);
      // Revert omitted for brevity
    }
  };

  const [analyzingLead, setAnalyzingLead] = useState<string | null>(null);

  const autoQualify = async (id: string) => {
    setAnalyzingLead(id);
    try {
      const response = await api.autoQualifyLead(id);
      const updates = response.data;
      setLeads(leads.map(l => l.id === id ? { ...l, ...updates } : l));
    } catch (error) {
      console.error("Failed to auto qualify lead", error);
    } finally {
      setAnalyzingLead(null);
    }
  };

  const getSemaforoColor = (color?: 'verde'|'amarillo'|'rojo') => {
    switch(color) {
      case 'verde': return 'bg-green-500/20 text-green-400 border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.1)]';
      case 'amarillo': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.1)]';
      case 'rojo': return 'bg-red-500/20 text-red-400 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.1)]';
      default: return 'bg-white/5 text-gray-400 border-white/10';
    }
  };

  const getNextStatus = (current: CRMLeadStatus): CRMLeadStatus | null => {
    const currentIndex = COLUMNAS.findIndex(c => c.id === current);
    if (currentIndex >= 0 && currentIndex < COLUMNAS.length - 1) {
      return COLUMNAS[currentIndex + 1].id;
    }
    return null;
  };

  const totalValue = leads.filter(l => l.estado !== 'ganado').reduce((acc, curr) => acc + curr.valor_mensual, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-10 h-10 text-ctx-teal animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-10 max-w-[1600px] mx-auto w-full">
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Pipeline de Ventas</h1>
          <p className="text-gray-400 text-sm">Gestiona el embudo de nuevos clientes de la agencia</p>
        </div>
        <div className="flex gap-4">
          <div className="glass-card px-4 py-2 flex flex-col border-ctx-teal/20">
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-rajdhani">Valor Total (En Pipeline)</span>
            <span className="text-lg font-orbitron font-bold text-white">{formatCOP(totalValue)}</span>
          </div>
          <button className="bg-ctx-teal hover:bg-teal-400 text-navy-dark font-bold px-6 py-2 rounded-xl transition-colors shadow-[0_0_15px_rgba(45,212,191,0.2)]">
            + Nuevo Lead
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 overflow-x-auto pb-4 custom-scrollbar min-h-[600px]">
        {COLUMNAS.map(columna => {
          const columnLeads = getLeadsByStatus(columna.id);
          const columnTotal = columnLeads.reduce((acc, curr) => acc + curr.valor_mensual, 0);
          
          return (
            <div key={columna.id} className="flex-1 min-w-[300px] flex flex-col bg-navy-light/30 border border-white/5 rounded-2xl p-4 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1" style={{ backgroundColor: columna.color.replace('text-', '') /* fallback */ }} />
              
              {/* Column Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <columna.icon className={`w-5 h-5 ${columna.color}`} />
                  <h3 className="font-rajdhani font-bold text-white uppercase tracking-wider">{columna.label}</h3>
                  <span className="bg-white/10 text-gray-300 text-xs px-2 py-0.5 rounded-full">{columnLeads.length}</span>
                </div>
                <button className="text-gray-500 hover:text-white transition-colors">
                  <MoreHorizontal className="w-4 h-4" />
                </button>
              </div>

              {/* Column Total */}
              <p className="text-sm font-bold text-gray-400 mb-4">{formatCOP(columnTotal)}</p>

              {/* Cards Container */}
              <div className="flex-1 flex flex-col gap-3">
                {columnLeads.map(lead => (
                  <motion.div layoutId={lead.id} key={lead.id}
                    className={`glass-card p-4 group cursor-pointer relative overflow-hidden border ${getSemaforoColor(lead.estado_semaforo)} transition-all duration-300`}>
                    
                    {analyzingLead === lead.id && (
                      <div className="absolute inset-0 bg-navy-dark/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center rounded-xl border border-ctx-teal/30">
                        <Loader2 className="w-6 h-6 text-ctx-teal animate-spin mb-2" />
                        <span className="text-xs text-ctx-teal font-rajdhani uppercase tracking-widest font-bold text-center px-2">Analizando huella digital...</span>
                      </div>
                    )}

                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-bold text-white text-sm">{lead.empresa}</h4>
                      <span className="text-xs text-white/80 font-bold bg-black/20 px-2 py-1 rounded-lg">{formatCOP(lead.valor_mensual)}</span>
                    </div>
                    <p className="text-xs text-gray-300 mb-3">{lead.contacto}</p>
                    
                    {/* Neurocontabilidad / AI Metrics */}
                    {lead.readiness_score !== undefined ? (
                      <div className="flex items-center gap-3 mb-3 bg-black/20 p-2 rounded-lg border border-white/5">
                        <div className="flex flex-col">
                          <span className="text-[9px] uppercase tracking-widest text-gray-400 mb-1">Readiness Score</span>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-black/40 rounded-full overflow-hidden">
                              <div className="h-full bg-ctx-teal" style={{ width: `${lead.readiness_score}%` }} />
                            </div>
                            <span className="text-xs font-bold text-white">{lead.readiness_score}</span>
                          </div>
                        </div>
                        {lead.riesgo_dian && (
                          <div className="flex flex-col border-l border-white/10 pl-3">
                            <span className="text-[9px] uppercase tracking-widest text-gray-400 mb-1">Riesgo DIAN</span>
                            <span className="text-xs font-bold flex items-center gap-1 text-white">
                              <AlertTriangle className="w-3 h-3" /> {lead.riesgo_dian}
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <button onClick={(e) => { e.stopPropagation(); autoQualify(lead.id); }}
                        className="w-full flex items-center justify-center gap-2 bg-ctx-teal/10 hover:bg-ctx-teal/20 text-ctx-teal border border-ctx-teal/30 py-2 rounded-lg mb-3 transition-colors text-xs font-bold uppercase tracking-widest font-rajdhani">
                        <Sparkles className="w-3 h-3" /> Auto-Calificar Lead
                      </button>
                    )}
                    
                    {/* Actions */}
                    <div className="flex justify-between items-center pt-2 border-t border-white/10 mt-auto">
                      <span className="text-[10px] text-gray-400">{lead.fecha_ingreso}</span>
                      
                      {getNextStatus(lead.estado) && (
                        <button 
                          onClick={(e) => { e.stopPropagation(); moveLead(lead.id, getNextStatus(lead.estado)!); }}
                          className="opacity-0 group-hover:opacity-100 flex items-center gap-1 text-[10px] text-white uppercase tracking-widest font-bold transition-opacity hover:text-ctx-teal"
                        >
                          Avanzar <ChevronRight className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
                
                {columnLeads.length === 0 && (
                  <div className="flex-1 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-xl min-h-[100px]">
                    <span className="text-xs">Sin leads</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
