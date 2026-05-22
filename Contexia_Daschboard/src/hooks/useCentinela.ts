/**
 * Custom hook for Centinela Fiscal data fetching.
 * 
 * Handles loading, error states, and auto-refresh for fiscal alerts.
 */

import { useState, useEffect, useCallback } from 'react';
import { centinelaApi } from '../services/api';

interface AlertaTributaria {
  nombre: string;
  porcentaje: number;
  valor_actual: number;
  umbral: number;
  severidad: 'roja' | 'amarilla' | 'verde';
  dias_estimados: number | null;
}

interface UseCentinelaReturn {
  alertas: AlertaTributaria[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useCentinela = (usuarioId: string | null): UseCentinelaReturn => {
  const [alertas, setAlertas] = useState<AlertaTributaria[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlertas = useCallback(async () => {
    if (!usuarioId) return;
    setLoading(true);
    try {
      const response = await centinelaApi.getAlertas(usuarioId);
      setAlertas(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar alertas fiscales');
    } finally {
      setLoading(false);
    }
  }, [usuarioId]);

  useEffect(() => {
    fetchAlertas();
    // Refresh every 10 minutes
    const interval = setInterval(fetchAlertas, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAlertas]);

  return { alertas, loading, error, refresh: fetchAlertas };
};
