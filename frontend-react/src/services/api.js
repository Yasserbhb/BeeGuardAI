/**
 * BeeGuardAI API Service
 * Handles all API calls to the backend
 */

const API_BASE = '/api';

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Include cookies for session
  };

  const response = await fetch(url, { ...defaultOptions, ...options });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================
// AUTH
// ============================================

export const auth = {
  login: (email, mot_de_passe) =>
    apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, mot_de_passe }),
    }),

  register: (data) =>
    apiCall('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  logout: () =>
    apiCall('/auth/logout', { method: 'POST' }),

  me: () => apiCall('/auth/me'),
};

// ============================================
// RUCHERS (APIARIES)
// ============================================

export const ruchers = {
  list: () => apiCall('/ruchers'),

  create: (nom, localisation) =>
    apiCall('/ruchers', {
      method: 'POST',
      body: JSON.stringify({ nom, localisation }),
    }),

  update: (id, data) =>
    apiCall(`/ruchers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id) =>
    apiCall(`/ruchers/${id}`, { method: 'DELETE' }),
};

// ============================================
// RUCHES
// ============================================

export const ruches = {
  list: () => apiCall('/ruches'),

  create: (nom, rucher_id = null) =>
    apiCall('/ruches', {
      method: 'POST',
      body: JSON.stringify({ nom, rucher_id }),
    }),

  update: (id, data) =>
    apiCall(`/ruches/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id) =>
    apiCall(`/ruches/${id}`, { method: 'DELETE' }),

  getData: (id, hours = 168, start = null, end = null) => {
    let url = `/ruches/${id}/donnees?hours=${hours}`;
    if (start && end) {
      url += `&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`;
    }
    return apiCall(url);
  },
};

// ============================================
// SENSOR DATA
// ============================================

export const data = {
  latest: () => apiCall('/donnees/latest'),

  send: (sensorData) =>
    apiCall('/donnees', {
      method: 'POST',
      body: JSON.stringify(sensorData),
    }),
};

// ============================================
// SETTINGS
// ============================================

export const settings = {
  get: () => apiCall('/settings'),

  update: (data) =>
    apiCall('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

export default { auth, ruchers, ruches, data, settings };
