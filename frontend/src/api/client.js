/**
 * Axios API client configured for Django backend.
 * Handles CSRF tokens and session cookies.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get CSRF token from cookie
function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return cookie.substring(name.length + 1);
    }
  }
  return '';
}

// Add CSRF token to mutating requests
api.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRFToken'] = getCSRFToken();
  }
  return config;
});

/* ═══ API Functions ═══ */

export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: () => api.post('/auth/logout/'),
  me: () => api.get('/auth/me/'),
};

export const sessionAPI = {
  start: () => api.post('/session/start/'),
  get: () => api.get('/session/'),
  reset: () => api.post('/session/reset/'),
  submitContext: (data) => api.post('/session/context/', data),
};

export const activityAPI = {
  submit: (activityNumber, data) =>
    api.post(`/activity/${activityNumber}/submit/`, data),
};

export const assessmentAPI = {
  getThinkingStyles: () => api.get('/thinking-styles/'),
  submitValidation: (domain, data) =>
    api.post(`/validation/${domain}/submit/`, data),
  getResults: () => api.get('/results/'),
  getRoadmap: (domain) => api.get(`/roadmap/${domain}/`),
};

export const deepDiveAPI = {
  getDomain: () => api.get('/deep-dive/domain/'),
  start: (domain) => api.post(`/deep-dive/${domain}/start/`),
  sendMessage: (domain, data) => api.post(`/deep-dive/${domain}/message/`, data),
  skip: (domain) => api.post(`/deep-dive/${domain}/skip/`),
};

export const analyticsAPI = {
  get: () => api.get('/analytics/'),
};

export default api;
