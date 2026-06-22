import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ComingSoonViewProps {
  icon: LucideIcon;
  titulo: string;
  subtitulo?: string;
}

export default function ComingSoonView({ icon: Icon, titulo, subtitulo = 'En construcción' }: ComingSoonViewProps) {
  return (
    <div className="w-full h-full min-h-[400px] flex flex-col items-center justify-center p-8 text-center animate-fadeInUp">
      <div className="w-24 h-24 mb-6 rounded-3xl bg-surface/40 border border-outline/30 flex items-center justify-center shadow-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-primary/10 group-hover:bg-primary/20 transition-colors duration-500"></div>
        <Icon className="w-10 h-10 text-primary opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all duration-500 relative z-10" />
      </div>
      <h2 className="text-3xl font-display font-bold text-ink mb-2 tracking-tight">
        {titulo}
      </h2>
      <p className="text-muted max-w-md mx-auto">
        {subtitulo}. Este módulo está siendo preparado por el equipo de ingeniería de Contexia y pronto estará disponible.
      </p>
      <div className="mt-8 flex gap-2 items-center justify-center">
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
        </span>
        <span className="text-[10px] font-bold uppercase tracking-widest text-primary">
          Próximamente
        </span>
      </div>
    </div>
  );
}
