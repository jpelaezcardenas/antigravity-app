import { useState } from 'react';
import { motion } from 'motion/react';
import { Settings, Building2, Receipt, Link2, Bell, Save } from 'lucide-react';
import { MOCK_CONFIG } from '../../data/mockData';

const Toggle = ({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) => (
  <button onClick={onToggle} className={`relative w-11 h-6 rounded-full transition-colors ${enabled ? 'bg-ctx-teal' : 'bg-white/10'}`}>
    <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-lg ${enabled ? 'left-[22px]' : 'left-0.5'}`} />
  </button>
);

export const ConfiguracionView = () => {
  const [config, setConfig] = useState(MOCK_CONFIG);
  const [saved, setSaved] = useState(false);

  const toggleIntegracion = (i: number) => {
    const updated = [...config.integraciones];
    updated[i] = { ...updated[i], conectado: !updated[i].conectado };
    setConfig({ ...config, integraciones: updated });
  };

  const toggleNotif = (key: keyof typeof config.notificaciones) => {
    setConfig({ ...config, notificaciones: { ...config.notificaciones, [key]: !config.notificaciones[key] } });
  };

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Perfil */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-ctx-teal/20"><Building2 className="w-5 h-5 text-ctx-teal" /></div>
          <h3 className="font-orbitron text-lg text-white">Perfil de Empresa</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: 'Nombre', value: config.empresa.nombre },
            { label: 'NIT', value: config.empresa.nit },
            { label: 'Plan', value: config.empresa.plan },
            { label: 'Email', value: config.empresa.email },
            { label: 'Teléfono', value: config.empresa.telefono },
            { label: 'Ciudad', value: config.empresa.ciudad },
          ].map(f => (
            <div key={f.label}>
              <label className="block text-[10px] text-gray-400 uppercase tracking-widest font-rajdhani mb-1">{f.label}</label>
              <input type="text" defaultValue={f.value} className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 px-4 text-sm text-white focus:outline-none focus:border-ctx-teal/50" />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Tributario */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-ctx-violet/20"><Receipt className="w-5 h-5 text-ctx-violet" /></div>
          <h3 className="font-orbitron text-lg text-white">Configuración Tributaria</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: '% Renta', value: config.tributario.porcentaje_renta, suffix: '%' },
            { label: '% IVA', value: config.tributario.porcentaje_iva, suffix: '%' },
            { label: 'Régimen', value: config.tributario.regimen },
            { label: 'Actividad Económica', value: config.tributario.actividad_economica },
            { label: 'Periodicidad IVA', value: config.tributario.periodicidad_iva },
          ].map(f => (
            <div key={f.label}>
              <label className="block text-[10px] text-gray-400 uppercase tracking-widest font-rajdhani mb-1">{f.label}</label>
              <input type="text" defaultValue={String(f.value)} className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 px-4 text-sm text-white focus:outline-none focus:border-ctx-teal/50" />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Integraciones */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-blue-500/20"><Link2 className="w-5 h-5 text-blue-400" /></div>
          <h3 className="font-orbitron text-lg text-white">Integraciones</h3>
        </div>
        <div className="space-y-3">
          {config.integraciones.map((integ, i) => (
            <div key={integ.nombre} className="flex items-center justify-between p-3 bg-white/[0.03] rounded-xl border border-white/5">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{integ.icono}</span>
                <div>
                  <p className="text-white font-bold text-sm">{integ.nombre}</p>
                  <p className={`text-[10px] uppercase tracking-widest ${integ.conectado ? 'text-green-400' : 'text-gray-500'}`}>
                    {integ.conectado ? 'Conectado' : 'Desconectado'}
                  </p>
                </div>
              </div>
              <Toggle enabled={integ.conectado} onToggle={() => toggleIntegracion(i)} />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Notificaciones */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-yellow-500/20"><Bell className="w-5 h-5 text-yellow-400" /></div>
          <h3 className="font-orbitron text-lg text-white">Notificaciones</h3>
        </div>
        <div className="space-y-3">
          {[
            { key: 'email' as const, label: 'Email', desc: 'Recibir alertas por correo' },
            { key: 'sms' as const, label: 'SMS', desc: 'Alertas por mensaje de texto' },
            { key: 'push' as const, label: 'Push', desc: 'Notificaciones en navegador' },
            { key: 'alertas_criticas' as const, label: 'Alertas Críticas', desc: 'Notificación inmediata para alertas rojas' },
            { key: 'resumen_semanal' as const, label: 'Resumen Semanal', desc: 'Reporte cada lunes por la mañana' },
          ].map(n => (
            <div key={n.key} className="flex items-center justify-between p-3 bg-white/[0.03] rounded-xl border border-white/5">
              <div>
                <p className="text-white font-bold text-sm">{n.label}</p>
                <p className="text-gray-500 text-xs">{n.desc}</p>
              </div>
              <Toggle enabled={config.notificaciones[n.key]} onToggle={() => toggleNotif(n.key)} />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Save */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="flex justify-end">
        <button onClick={handleSave}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all ${
            saved ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'premium-button'
          }`}>
          {saved ? <><span>✅</span> Guardado</> : <><Save className="w-4 h-4" /> Guardar Cambios</>}
        </button>
      </motion.div>
    </div>
  );
};
