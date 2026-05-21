import type { ReactNode } from "react";

interface TatyTipCardProps {
  title: string;
  children: ReactNode;
  variant?: "info" | "violet";
}

export function TatyTipCard({ title, children, variant = "info" }: TatyTipCardProps) {
  const accent =
    variant === "violet"
      ? {
          border: "border-[#8B5CF6]/30",
          bar: "bg-[#8B5CF6]",
          icon: "text-[#8B5CF6]",
          glow: "shadow-[0_0_20px_rgba(139,92,246,0.1)]",
        }
      : {
          border: "border-[#2DD4BF]/30",
          bar: "bg-[#2DD4BF]",
          icon: "text-[#2DD4BF]",
          glow: "shadow-[0_0_20px_rgba(45,212,191,0.1)]",
        };

  return (
    <div
      className={`relative bg-white/[0.03] border ${accent.border} rounded-xl p-4 backdrop-blur-md overflow-hidden ${accent.glow}`}
    >
      <div className={`absolute top-0 left-0 w-1 h-full ${accent.bar}`} />
      <div className="flex gap-3 items-start">
        <div className="flex-shrink-0 w-10 h-12 rounded-lg overflow-hidden border border-white/10 shadow-md">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/assets/img/profiles/tatiana_full.png"
            alt="Taty"
            className="w-full h-full object-cover object-top"
          />
        </div>
        <div className="flex-1 min-w-0">
          <p
            className={`text-[10px] font-bold uppercase tracking-widest ${accent.icon} mb-1`}
            style={{ fontFamily: "Rajdhani, sans-serif" }}
          >
            Taty te explica
          </p>
          <p className="text-sm text-white font-bold mb-1">{title}</p>
          <div className="text-[13px] text-on-surface-variant leading-relaxed">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
