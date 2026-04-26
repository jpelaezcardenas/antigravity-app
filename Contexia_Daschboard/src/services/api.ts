import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir el token si existe
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('contexia_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (credentials: any) => apiClient.post('/auth/login', credentials),
};

export const pulsoApi = {
  getDiario: (usuarioId: string, fecha?: string) => 
    apiClient.get(`/pulso/diario`, { params: { usuario_id: usuarioId, fecha } }),
};

export const alertasApi = {
  getTributarias: (usuarioId: string) => 
    apiClient.get(`/alertas/tributarias`, { params: { usuario_id: usuarioId } }),
};

export default apiClient;
