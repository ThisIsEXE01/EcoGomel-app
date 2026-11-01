/**
 * Единый клиент для запросов к Django API.
 * Подключается обычным <script> до скриптов страниц.
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

async function apiRequest(path, params = {}) {
  const url = new URL(`${API_BASE_URL}/${path}/`);

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
  getWaste: (params) => apiRequest('waste', params),
  getWasteItem: (id) => apiRequest(`waste/${id}`),
  getPoints: (params) => apiRequest('points', params),
};
