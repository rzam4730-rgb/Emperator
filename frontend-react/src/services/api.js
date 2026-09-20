const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('emperator_access_token');
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await response.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }

  if (!response.ok) {
    const message = data.detail || data.message || 'خطا در ارتباط با سرور';
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return data;
}

export async function login(phone, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone, password })
  });
}

export async function register(payload) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export { API_BASE };
