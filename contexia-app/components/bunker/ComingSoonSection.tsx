"use client";

export function ComingSoonSection({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-24 px-6">
      <div className="w-14 h-14 rounded-full card-premium flex items-center justify-center mb-4 glow-teal-soft">
        <span className="material-symbols-outlined text-primary text-2xl">
          construction
        </span>
      </div>
      <h2 className="font-title-md text-title-md text-gradient mb-2">
        {label}
      </h2>
      <p className="font-body-md text-body-md text-on-surface-variant max-w-sm">
        Esta sección está en construcción. Muy pronto estará disponible.
      </p>
    </div>
  );
}
