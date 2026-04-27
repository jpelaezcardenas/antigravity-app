import { Suspense } from "react";
import WizardClient from "./wizard-client";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#f8fafc",
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                border: "3px solid #e2e8f0",
                borderTopColor: "#00a878",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
                margin: "0 auto 1rem",
              }}
            />
            <p style={{ color: "#64748b" }}>Cargando Shadow Audit...</p>
          </div>
        </div>
      }
    >
      <WizardClient />
    </Suspense>
  );
}
