/**
 * Единый клиент для запросов к Django API.
 * Автоматически подстраивается под локальный запуск (file://) и серверный (/api).
 */

// Если открыли файл напрямую — стучимся на 127.0.0.1:8000, иначе используем относительный /api
const isFileProtocol = window.location.protocol === 'file:';
const API_BASE_URL = isFileProtocol ? 'http://127.0.0.1:8000/api' : '/api';

async function apiRequest(path, params = {}) {
  let url;
  if (isFileProtocol) {
    url = new URL(`${API_BASE_URL}/${path}/`);
  } else {
    url = new URL(`${API_BASE_URL}/${path}/`, window.location.origin);
  }

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API ${url.pathname}: ${response.status}`);
  }

  return response.json();
}

const EcoAPI = {
  BASE_URL: API_BASE_URL,
  getWaste: (params) => apiRequest('waste', params),
  getWasteItem: (id) => apiRequest(`waste/${id}`),
  getPoints: (params) => apiRequest('points', params),
};