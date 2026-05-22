/**
 * Contexia API Client
 * 
 * Centralized Axios instance with:
 * - JWT injection via request interceptor
 * - Automatic token expiry handling (401 → redirect to login)
 * - Typed API methods organized by module
 */

import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.contexia.online/api/v1';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // 15 second timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// --- Request Interceptor: Inject JWT ---
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// --- Response Interceptor: Handle 401 (expired/invalid token) ---
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — clear session and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Only redirect if we're not already on the login page
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/app/';
      }
    }
    return Promise.reject(error);
  },
);


// --- Auth API ---
export const authApi = {
  login: (credentials: { email: string; password: string }) =>
    api.post<{ token: string; usuario_id: string; nombre_empresa: string }>(
      '/auth/login',
      credentials,
    ),
};

// --- Pulso API ---
export const pulsoApi = {
  getPulso: (usuarioId: string) =>
    api.get(`/pulso/${usuarioId}`),
};

// --- Centinela API ---
export const centinelaApi = {
  getAlertas: (usuarioId: string) =>
    api.get(`/centinela/${usuarioId}`),
};

// --- Cobro API ---
export const cobroApi = {
  getCartera: (usuarioId: string) =>
    api.get(`/cobro/${usuarioId}`),
  
  registrarIntento: (usuarioId: string, data: {
    factura_id: string;
    tipo_evento: string;
    resultado: string;
    monto_comprometido?: number;
    fecha_pago_comprometida?: string;
  }) =>
    api.post(`/cobro/${usuarioId}/intento`, data),
  
  generarCarta: (usuarioId: string, data: { factura_id: string; tipo: string }) =>
    api.post<{ contenido: string }>(`/cobro/${usuarioId}/carta`, data),
};

export default api;
