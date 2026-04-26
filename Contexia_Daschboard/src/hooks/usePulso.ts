import { useState, useEffect } from 'react';
import { pulsoApi } from '../services/api';

export const usePulso = (usuarioId: string | null) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPulso = async () => {
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
  };

  useEffect(() => {
    fetchPulso();
    // Refresh cada 5 minutos
    const interval = setInterval(fetchPulso, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [usuarioId]);

  return { data, loading, error, refresh: fetchPulso };
};
