import React, { useState, useEffect } from 'react';

interface OsStatus {
  os: string;
  version: string;
  backend_health: {
    url: string;
    status_code: number | null;
    healthy: boolean;
    response_time_ms?: number;
    body?: string;
    error?: string;
  };
  hermes: {
    profile: string;
    model: string;
    provider: string;
  };
  providers: {
    chain: Array<{ provider: string; available: boolean }>;
    available: number;
    total: number;
    _error?: string;
  };
  active_skills: string[];
  gateway: {
    running: boolean;
  };
  timestamp: string;
}

const AgenticOpsView: React.FC = () => {
  const [status, setStatus] = useState<OsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/hermes/os-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      setStatus(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="card-premium p-6">
        <p className="text-muted">Cargando status del Agentic OS...</p>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="card-premium p-6 border-warning">
        <p className="text-warning">Error: {error}</p>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-display font-bold text-primary">Contexia Agentic OS</h1>
        <div className="text-xs text-muted">
          {lastUpdate && `Última actualización: ${lastUpdate.toLocaleTimeString('es-CO')}`}
        </div>
      </div>

      {/* Overall Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend */}
        <div className="card-premium p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${status.backend_health.healthy ? 'bg-success' : 'bg-warning'}`} />
            <p className="text-xs uppercase tracking-wide text-muted">Backend</p>
          </div>
          <p className="text-lg font-semibold text-primary">
            {status.backend_health.status_code || '—'}
          </p>
          {status.backend_health.response_time_ms && (
            <p className="text-xs text-muted mt-1">{status.backend_health.response_time_ms}ms</p>
          )}
          {status.backend_health.error && (
            <p className="text-xs text-warning mt-1">{status.backend_health.error}</p>
          )}
        </div>

        {/* Hermes Profile */}
        <div className="card-premium p-4">
          <p className="text-xs uppercase tracking-wide text-muted mb-2">Perfil</p>
          <p className="text-lg font-semibold text-primary">{status.hermes.profile}</p>
          <p className="text-xs text-muted mt-1">v{status.version}</p>
        </div>

        {/* Model */}
        <div className="card-premium p-4">
          <p className="text-xs uppercase tracking-wide text-muted mb-2">Modelo</p>
          <p className="text-sm font-mono text-secondary truncate">
            {status.hermes.model.split('/').pop()}
          </p>
          <p className="text-xs text-muted mt-1">{status.hermes.provider}</p>
        </div>

        {/* Gateway */}
        <div className="card-premium p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${status.gateway.running ? 'bg-success' : 'bg-warning'}`} />
            <p className="text-xs uppercase tracking-wide text-muted">Gateway</p>
          </div>
          <p className="text-lg font-semibold text-primary">
            {status.gateway.running ? '✓ Online' : '✗ Offline'}
          </p>
        </div>
      </div>

      {/* Providers Chain */}
      <div className="card-premium p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">LLM Provider Chain</h2>
        {status.providers._error ? (
          <p className="text-warning text-sm">{status.providers._error}</p>
        ) : (
          <div>
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl font-display font-bold text-success">{status.providers.available}</span>
                <span className="text-sm text-muted">/ {status.providers.total} disponibles</span>
              </div>
            </div>
            <div className="space-y-2">
              {status.providers.chain.map((p) => (
                <div
                  key={p.provider}
                  className="flex items-center justify-between p-2 bg-white/5 rounded border border-outline/20"
                >
                  <span className="text-sm font-mono capitalize">{p.provider}</span>
                  <div className={`w-2 h-2 rounded-full ${p.available ? 'bg-success' : 'bg-outline/40'}`} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Active Skills */}
      <div className="card-premium p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">Contexia Skills ({status.active_skills.length})</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {status.active_skills.map((skill) => (
            <div key={skill} className="p-2 bg-primary/10 border border-primary/20 rounded text-xs">
              <code className="text-primary">{skill.replace('contexia-', '')}</code>
            </div>
          ))}
        </div>
      </div>

      {/* Raw Data (debug) */}
      <div className="card-premium p-6">
        <details className="cursor-pointer">
          <summary className="text-sm text-muted uppercase tracking-wide hover:text-primary transition">
            📋 Datos crudos
          </summary>
          <pre className="mt-4 p-3 bg-obsidian text-xs overflow-x-auto rounded border border-outline/20">
            {JSON.stringify(status, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );
};

export default AgenticOpsView;
