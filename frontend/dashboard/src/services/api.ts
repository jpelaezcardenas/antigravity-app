import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.contexia.online/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el token JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (credentials: any) => api.post('/auth/login', credentials),
};

export const pulsoApi = {
  getPulso: (usuarioId: string) => api.get(`/pulso/${usuarioId}`),
};

export const centinelaApi = {
  getAlertas: (usuarioId: string) => api.get(`/centinela/${usuarioId}`),
};

export const cobroApi = {
  getCartera: (usuarioId: string) => api.get(`/cobro/${usuarioId}`),
  registrarIntento: (usuarioId: string, data: any) => api.post(`/cobro/${usuarioId}/intento`, data),
  generarCarta: (usuarioId: string, data: any) => api.post(`/cobro/${usuarioId}/carta`, data),
};

export default api;
