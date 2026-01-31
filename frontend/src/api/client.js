import axios from 'axios';

// URL бэкенда - пока localhost, потом заменишь на production
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем Telegram данные к каждому запросу
api.interceptors.request.use((config) => {
  const tg = window.Telegram?.WebApp;
  
  if (tg?.initData) {
    config.headers['X-Telegram-Init-Data'] = tg.initData;
  }
  
  console.log('🚀 API Request:', config.method?.toUpperCase(), config.url, config.data);
  return config;
});

// Логируем ответы и ошибки
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.config.url, response.data);
    return response;
  },
  (error) => {
    console.error('❌ API Error:', error.config?.url, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ===== USER API =====
export const userApi = {
  getMe: () => api.get('/users/me'),
  updateSettings: (data) => api.patch('/users/me', data),
  getStats: () => api.get('/users/me/stats'),
};

// ===== REMINDERS API =====
export const remindersApi = {
  getAll: (params = {}) => api.get('/reminders', { params }),
  getToday: () => api.get('/reminders/today'),
  getOne: (id) => api.get(`/reminders/${id}`),
  create: (data) => api.post('/reminders', data),
  update: (id, data) => api.patch(`/reminders/${id}`, data),
  complete: (id) => api.post(`/reminders/${id}/complete`),
  delete: (id) => api.delete(`/reminders/${id}`),
  parse: (text) => api.post('/reminders/parse', { text }),
};

// ===== CATEGORIES API =====
export const categoriesApi = {
  getAll: () => api.get('/categories'),
  create: (data) => api.post('/categories', data),
  update: (id, data) => api.patch(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
};

export default api;