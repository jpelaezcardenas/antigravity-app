import { motion } from 'motion/react';
import { Radar, Search, Mail, Sparkles } from 'lucide-react';
import { useState } from 'react';

interface ComingSoonViewProps {
  icon: 'auditoria' | 'radar';
  titulo: string;
  subtitulo: string;
  descripcion: string;
  features: string[];
}

export const ComingSoonView = ({ icon, titulo, subtitulo, descripcion, features }: ComingSoonViewProps) => {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const IconComp = icon === 'auditoria' ? Search : Radar;

  return (
    <div className="max-w-3xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-10 md:p-16 text-center relative overflow-hidden"
      >
        {/* Background effects */}
        <div className="absolute top-[-20%] right-[-20%] w-[60%] h-[60%] bg-ctx-violet/5 blur-[100px] rounded-full" />
        <div className="absolute bottom-[-20%] left-[-20%] w-[60%] h-[60%] bg-ctx-teal/5 blur-[100px] rounded-full" />

        <div className="relative z-10">
          {/* Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
            className="w-24 h-24 rounded-3xl bg-gradient-to-br from-ctx-teal/20 to-ctx-violet/20 flex items-center justify-center mx-auto mb-8 border border-white/10"
          >
            <IconComp className="w-12 h-12 text-ctx-teal" />
          </motion.div>

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-ctx-violet/10 border border-ctx-violet/20 rounded-full mb-6">
              <Sparkles className="w-3 h-3 text-ctx-violet" />
              <span className="text-[10px] text-ctx-violet uppercase tracking-widest font-bold">Próximamente</span>
            </div>

            <h2 className="font-orbitron text-2xl md:text-3xl font-bold text-white mb-3">
              {titulo}
            </h2>
            <p className="text-ctx-teal text-sm font-rajdhani uppercase tracking-widest mb-6">
              {subtitulo}
            </p>
            <p className="text-gray-400 max-w-lg mx-auto mb-8 leading-relaxed">
              {descripcion}
            </p>
          </motion.div>

          {/* Features */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-wrap justify-center gap-3 mb-10"
          >
            {features.map((f, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-gray-300"
              >
                {f}
              </span>
            ))}
          </motion.div>

          {/* Waitlist */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            {subscribed ? (
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="inline-flex items-center gap-2 px-6 py-3 bg-green-500/10 border border-green-500/20 rounded-xl"
              >
                <span className="text-lg">✅</span>
                <span className="text-green-400 font-bold text-sm">¡Te avisaremos cuando esté listo!</span>
              </motion.div>
            ) : (
              <div className="flex flex-col sm:flex-row items-center gap-3 max-w-md mx-auto">
                <div className="relative flex-1 w-full">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu@email.com"
                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-ctx-teal/50 transition-colors"
                  />
                </div>
                <button
                  onClick={() => setSubscribed(true)}
                  className="premium-button px-6 py-3 text-sm w-full sm:w-auto flex-shrink-0"
                >
                  Avísame
                </button>
              </div>
            )}
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};
