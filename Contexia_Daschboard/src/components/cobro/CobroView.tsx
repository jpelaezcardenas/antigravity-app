import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mail, Phone, FileText, X, DollarSign, AlertTriangle, Clock } from 'lucide-react';
import { MOCK_CARTERA, formatCOP, type FacturaVencida } from '../../data/mockData';

const getSeveridad = (dias: number) => {
  if (dias >= 45) return { label: 'Crítica', color: 'red', bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' };
  if (dias >= 15) return { label: 'Urgente', color: 'yellow', bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' };
  return { label: 'Normal', color: 'green', bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' };
};

const CobroModal = ({ factura, onClose }: { factura: FacturaVencida; onClose: () => void }) => {
  const [tipo, setTipo] = useState('llamada');
  const [resultado, setResultado] = useState('');
  const [saved, setSaved] = useState(false);
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <motion.div initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }} onClick={e => e.stopPropagation()} className="glass-card p-6 max-w-md w-full border-ctx-teal/20">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-orbitron text-lg">Registrar Gestión</h3>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition-colors"><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <div className="mb-4">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Factura</p>
          <p className="text-white font-bold">{factura.numero_factura} — {factura.cliente}</p>
          <p className="text-ctx-teal font-orbitron text-lg">{formatCOP(factura.monto)}</p>
        </div>
        {saved ? (
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">✅</span>
            </div>
            <p className="text-green-400 font-bold">¡Gestión registrada!</p>
            <p className="text-gray-400 text-sm mt-1">Se guardó exitosamente</p>
          </motion.div>
        ) : (
          <>
            <div className="mb-4">
              <p className="text-xs text-gray-400 uppercase tracking-widest mb-2">Tipo de gestión</p>
              <div className="flex gap-2">
                {[{id: 'llamada', icon: Phone, label: 'Llamada'}, {id: 'email', icon: Mail, label: 'Email'}, {id: 'carta', icon: FileText, label: 'Carta'}].map(t => (
                  <button key={t.id} onClick={() => setTipo(t.id)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl border text-xs font-bold uppercase tracking-wider transition-all ${tipo === t.id ? 'bg-ctx-teal/10 border-ctx-teal/30 text-ctx-teal' : 'border-white/10 text-gray-400 hover:bg-white/5'}`}>
                    <t.icon className="w-3 h-3" />{t.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-6">
              <p className="text-xs text-gray-400 uppercase tracking-widest mb-2">Resultado</p>
              <select value={resultado} onChange={e => setResultado(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 px-4 text-white text-sm focus:outline-none focus:border-ctx-teal/50 appearance-none">
                <option value="" className="bg-navy-dark">Seleccionar...</option>
                <option value="no_contesta" className="bg-navy-dark">No contesta</option>
                <option value="promesa" className="bg-navy-dark">Promesa de pago</option>
                <option value="rechaza" className="bg-navy-dark">Rechaza pago</option>
                <option value="parcial" className="bg-navy-dark">Acuerdo parcial</option>
              </select>
            </div>
            <button onClick={() => setSaved(true)} className="premium-button w-full py-3 text-sm">Guardar Gestión</button>
          </>
        )}
      </motion.div>
    </motion.div>
  );
};

const CartaPreview = ({ factura, onClose }: { factura: FacturaVencida; onClose: () => void }) => {
  const [tipo, setTipo] = useState<'amistosa' | 'oficial' | 'judicial'>('amistosa');
  const templates = {
    amistosa: `Estimado/a cliente,\n\nLe recordamos amablemente que la factura ${factura.numero_factura} por valor de ${formatCOP(factura.monto)} se encuentra vencida desde hace ${factura.dias_vencida} días.\n\nAgradecemos su pronta gestión de pago.\n\nCordialmente,\nFerez.com E-comerce`,
    oficial: `REQUERIMIENTO DE PAGO\n\nRef: Factura ${factura.numero_factura}\n\nPor medio de la presente, le requerimos formalmente el pago de la suma de ${formatCOP(factura.monto)}, correspondiente a la factura en referencia, la cual se encuentra vencida hace ${factura.dias_vencida} días.\n\nDe no recibir el pago en los próximos 10 días hábiles, nos veremos en la obligación de iniciar acciones legales.\n\nAtentamente,\nFerez.com E-comerce`,
    judicial: `AVISO PREVIO A ACCIÓN JUDICIAL\n\nRef: Cobro de Factura ${factura.numero_factura}\n\nSe le informa que, ante el incumplimiento reiterado en el pago de ${formatCOP(factura.monto)}, vencida hace ${factura.dias_vencida} días, procederemos a instaurar las acciones legales pertinentes en un plazo de 5 días hábiles.\n\nEste aviso se constituye como requerimiento previo conforme a la legislación colombiana vigente.\n\nFerez.com E-comerce\nÁrea Jurídica`,
  };
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }} onClick={e => e.stopPropagation()} className="glass-card p-6 max-w-lg w-full border-ctx-violet/20 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-orbitron text-lg">📧 Carta de Cobro</h3>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg"><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <div className="flex gap-2 mb-4">
          {(['amistosa', 'oficial', 'judicial'] as const).map(t => (
            <button key={t} onClick={() => setTipo(t)}
              className={`flex-1 py-2 rounded-xl border text-xs font-bold uppercase tracking-wider transition-all ${tipo === t ? 'bg-ctx-violet/10 border-ctx-violet/30 text-ctx-violet' : 'border-white/10 text-gray-400 hover:bg-white/5'}`}>
              {t}
            </button>
          ))}
        </div>
        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{templates[tipo]}</pre>
        </div>
        <button className="premium-button w-full py-3 text-sm mt-4">Copiar al Portapapeles</button>
      </motion.div>
    </motion.div>
  );
};

export const CobroView = () => {
  const [modalFactura, setModalFactura] = useState<FacturaVencida | null>(null);
  const [cartaFactura, setCartaFactura] = useState<FacturaVencida | null>(null);
  const totalVencido = MOCK_CARTERA.reduce((s, f) => s + f.monto, 0);
  const criticas = MOCK_CARTERA.filter(f => f.dias_vencida >= 45);
  const urgentes = MOCK_CARTERA.filter(f => f.dias_vencida >= 15 && f.dias_vencida < 45);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Total Vencido', value: formatCOP(totalVencido), icon: DollarSign, color: 'red' },
          { label: 'Críticas (45+ días)', value: `${criticas.length} facturas`, icon: AlertTriangle, color: 'red' },
          { label: 'Urgentes (15-44 días)', value: `${urgentes.length} facturas`, icon: Clock, color: 'yellow' },
        ].map((m, i) => (
          <motion.div key={m.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
            className={`glass-card p-5 border-${m.color}-500/20`}>
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-xl bg-${m.color}-500/20`}><m.icon className={`w-5 h-5 text-${m.color}-400`} /></div>
              <span className="text-[10px] text-gray-400 uppercase tracking-widest font-rajdhani">{m.label}</span>
            </div>
            <p className="text-xl font-orbitron font-bold text-white">{m.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Desktop Table */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="glass-card overflow-hidden hidden md:block">
        <div className="p-5 border-b border-white/5">
          <h3 className="font-orbitron text-lg">Facturas Vencidas</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Factura', 'Cliente', 'Monto', 'Días', 'Estado', 'Acciones'].map(h => (
                  <th key={h} className="text-left py-3 px-4 text-[10px] text-gray-400 uppercase tracking-widest font-rajdhani">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_CARTERA.map(f => {
                const sev = getSeveridad(f.dias_vencida);
                return (
                  <tr key={f.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-sm font-mono text-gray-300">{f.numero_factura}</td>
                    <td className="py-3 px-4 text-sm text-white">{f.cliente}</td>
                    <td className="py-3 px-4 text-sm font-orbitron text-white">{formatCOP(f.monto)}</td>
                    <td className="py-3 px-4"><span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${sev.bg} ${sev.text}`}>{f.dias_vencida}d</span></td>
                    <td className="py-3 px-4"><span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${sev.bg} ${sev.text}`}>{sev.label}</span></td>
                    <td className="py-3 px-4">
                      <div className="flex gap-1">
                        <button onClick={() => setCartaFactura(f)} className="p-1.5 hover:bg-white/10 rounded-lg transition-colors" title="Enviar Carta"><Mail className="w-4 h-4 text-gray-400" /></button>
                        <button onClick={() => setModalFactura(f)} className="p-1.5 hover:bg-white/10 rounded-lg transition-colors" title="Registrar Llamada"><Phone className="w-4 h-4 text-gray-400" /></button>
                        <button className="p-1.5 hover:bg-white/10 rounded-lg transition-colors" title="Ver Historial"><FileText className="w-4 h-4 text-gray-400" /></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Mobile Cards */}
      <div className="space-y-3 md:hidden">
        {MOCK_CARTERA.map((f, i) => {
          const sev = getSeveridad(f.dias_vencida);
          return (
            <motion.div key={f.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.05 }}
              className={`glass-card p-4 ${sev.border}`}>
              <div className="flex justify-between items-start mb-2">
                <span className="font-mono text-xs text-gray-400">{f.numero_factura}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${sev.bg} ${sev.text}`}>{f.dias_vencida}d</span>
              </div>
              <p className="text-white font-bold text-sm mb-1">{f.cliente}</p>
              <p className="font-orbitron text-lg text-white mb-3">{formatCOP(f.monto)}</p>
              <div className="flex gap-2">
                <button onClick={() => setCartaFactura(f)} className="flex-1 flex items-center justify-center gap-1 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-gray-300 hover:bg-white/10"><Mail className="w-3 h-3" /> Carta</button>
                <button onClick={() => setModalFactura(f)} className="flex-1 flex items-center justify-center gap-1 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-gray-300 hover:bg-white/10"><Phone className="w-3 h-3" /> Llamada</button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Modals */}
      <AnimatePresence>
        {modalFactura && <CobroModal factura={modalFactura} onClose={() => setModalFactura(null)} />}
        {cartaFactura && <CartaPreview factura={cartaFactura} onClose={() => setCartaFactura(null)} />}
      </AnimatePresence>
    </div>
  );
};
