/**
 * Custom hook for Pulso Diario data fetching.
 * 
 * Handles loading, error states, and auto-refresh (every 5 minutes)
 * for the financial pulse dashboard.
 */

import { useState, useEffect, useCallback } from 'react';
import { pulsoApi } from '../services/api';

interface PulsoDiario {
  fecha: string;
  ingresos: number;
  gastos: number;
  margen: number;
  provision_dian: number;
  dinero_tuyo_hoy: number;
  advertencias: string[];
}

interface UsePulsoReturn {
  data: PulsoDiario | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const usePulso = (usuarioId: string | null): UsePulsoReturn => {
  const [data, setData] = useState<PulsoDiario | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPulso = useCallback(async () => {
    if (!usuarioId) return;
    setLoading(true);
    try {
      const response = await pulsoApi.getPulso(usuarioId);
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar el pulso');
    } finally {
      setLoading(false);
    }
  }, [usuarioId]);

  useEffect(() => {
    fetchPulso();
    // Refresh every 5 minutes
    const interval = setInterval(fetchPulso, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchPulso]);

  return { data, loading, error, refresh: fetchPulso };
};
