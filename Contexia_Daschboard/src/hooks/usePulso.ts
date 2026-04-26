import { useState, useEffect } from 'react';
import { pulsoApi } from '../services/api';

export interface PulsoData {
  fecha: string;
  ingresos_hoy: number;
  gastos_hoy: number;
  margen_hoy: number;
  provision_dian: number;
  dinero_tuyo_hoy: number;
  advertencias: string[];
}

export const usePulso = (usuarioId: string | null) => {
  const [pulso, setPulso] = useState<PulsoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPulso = async () => {
    if (!usuarioId) return;
    try {
      setLoading(true);
      const response = await pulsoApi.getDiario(usuarioId);
      setPulso(response.data);
    } catch (err: any) {
      setError(err.message || 'Error al cargar el pulso');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPulso();
  }, [usuarioId]);

  return { pulso, loading, error, refresh: fetchPulso };
};
