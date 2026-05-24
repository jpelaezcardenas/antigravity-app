"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface DemoAccount {
  email: string;
  password: string;
  company: string;
  description: string;
}

const demoAccounts: DemoAccount[] = [
  {
    email: "jpelaezcardenas@gmail.com",
    password: "demo123456",
    company: "Contexia",
    description: "Accounting • Enterprise • Envigado",
  },
  {
    email: "fperez@ferez.co",
    password: "demo123456",
    company: "FEREZ SAS",
    description: "E-commerce • Growth • Medellín",
  },
  {
    email: "carlos@importacionesmtz.co",
    password: "demo123456",
    company: "Importaciones Martinez",
    description: "E-commerce • Growth • Cali",
  },
];

export default function AuthPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Demo authentication - check against demo accounts
      const account = demoAccounts.find(
        (acc) => acc.email === email && acc.password === password
      );

      if (!account) {
        throw new Error("Email o contraseña incorrectos");
      }

      // Store user data in localStorage
      const userData = {
        email: account.email,
        company_name: account.company,
        usuario_id: `user_${Date.now()}`,
      };
      localStorage.setItem("cx_user", JSON.stringify(userData));
      localStorage.setItem("auth_token", `token_${Date.now()}`);

      // Redirect to app
      router.push("/app/overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en login");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (account: DemoAccount) => {
    setError("");
    setLoading(true);

    try {
      const userData = {
        email: account.email,
        company_name: account.company,
        usuario_id: `user_${Date.now()}`,
      };
      localStorage.setItem("cx_user", JSON.stringify(userData));
      localStorage.setItem("auth_token", `token_${Date.now()}`);
      router.push("/app/overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Contexia</h1>
          <p className="text-purple-300 text-sm">Tax Intelligence Platform</p>
        </div>

        {/* Login Form Card */}
        <div className="bg-white bg-opacity-10 backdrop-blur-xl rounded-2xl p-8 border border-white border-opacity-20 shadow-xl">
          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg flex items-start gap-3">
              <span className="text-red-400 flex-shrink-0 mt-0.5">⚠️</span>
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-4 mb-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-200 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                placeholder="your@email.com"
                className="w-full px-4 py-2.5 bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-opacity-20 transition disabled:opacity-50"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-200 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-opacity-20 transition disabled:opacity-50"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Ingresando...
                </>
              ) : (
                "Ingresar"
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-white bg-opacity-10"></div>
            <span className="text-gray-400 text-xs font-medium">O PRUEBA DEMO</span>
            <div className="flex-1 h-px bg-white bg-opacity-10"></div>
          </div>

          {/* Demo Accounts */}
          <div className="space-y-3">
            {demoAccounts.map((account, index) => (
              <button
                key={index}
                onClick={() => handleDemoLogin(account)}
                disabled={loading}
                type="button"
                className="w-full text-left p-4 bg-white bg-opacity-5 hover:bg-opacity-10 border border-white border-opacity-10 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed hover:scale-102"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-white">{account.company}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{account.description}</p>
                  </div>
                  {loading && (
                    <span className="animate-spin text-purple-400">⏳</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center">
          <p className="text-gray-400 text-xs">
            Todas las cuentas demo usan: <span className="font-mono text-purple-300">demo123456</span>
          </p>
          <p className="text-gray-500 text-xs mt-2">
            Ambiente de demostración con datos fiscales colombianos
          </p>
        </div>
      </div>
    </div>
  );
}
