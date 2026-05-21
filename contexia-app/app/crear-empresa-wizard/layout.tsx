import type { ReactNode } from "react";

export default function CrearEmpresaWizardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      className="min-h-screen flex flex-col text-on-surface"
      style={{
        backgroundColor: "#020617",
        backgroundImage:
          "radial-gradient(circle at 15% 10%, rgba(45, 212, 191, 0.08) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(139, 92, 246, 0.06) 0%, transparent 50%)",
      }}
    >
      {children}
    </div>
  );
}
