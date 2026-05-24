"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem("auth_token");
    const user = localStorage.getItem("cx_user");

    if (token && user) {
      // User is authenticated, redirect to app
      router.push("/app/overview");
    } else {
      // User is not authenticated, redirect to login
      router.push("/auth");
    }
  }, [router]);

  // Show loading state while checking auth
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin text-4xl mb-4">⏳</div>
        <p className="text-white">Verificando autenticación...</p>
      </div>
    </div>
  );
}
