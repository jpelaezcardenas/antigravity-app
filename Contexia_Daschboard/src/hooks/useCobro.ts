/**
 * Custom hook for Cobro (Collections) data fetching.
 * 
 * Manages overdue invoices, collection attempts, and letter generation.
 */

import { useState, useEffect, useCallback } from 'react';
import { cobroApi } from '../services/api';

interface AlertaCobro {
  factura_id: string;
  cliente: string;
  dias_vencidos: number;
  monto: number;
  nivel_urgencia: 'bajo' | 'medio' | 'alto';
}

interface UseCobroReturn {
  cartera: AlertaCobro[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  registrarIntento: (data: any) => Promise<boolean>;
  generarCarta: (facturaId: string, tipo: string) => Promise<string | null>;
}

export const useCobro = (usuarioId: string | null): UseCobroReturn => {
  const [cartera, setCartera] = useState<AlertaCobro[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCartera = useCallback(async () => {
    if (!usuarioId) return;
    setLoading(true);
    try {
      const response = await cobroApi.getCartera(usuarioId);
      setCartera(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar cartera');
    } finally {
      setLoading(false);
    }
  }, [usuarioId]);

  const registrarIntento = useCallback(async (data: any): Promise<boolean> => {
    if (!usuarioId) return false;
    try {
      await cobroApi.registrarIntento(usuarioId, data);
      await fetchCartera(); // Refresh after registering
      return true;
    } catch {
      return false;
    }
  }, [usuarioId, fetchCartera]);

  const generarCarta = useCallback(async (facturaId: string, tipo: string): Promise<string | null> => {
    if (!usuarioId) return null;
    try {
      const response = await cobroApi.generarCarta(usuarioId, { factura_id: facturaId, tipo });
      return response.data.contenido;
    } catch {
      return null;
    }
  }, [usuarioId]);

  useEffect(() => {
    fetchCartera();
    const interval = setInterval(fetchCartera, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchCartera]);

  return { cartera, loading, error, refresh: fetchCartera, registrarIntento, generarCarta };
};
