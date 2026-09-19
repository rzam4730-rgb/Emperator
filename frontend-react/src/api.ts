const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer' | string;
};

export type DashboardData = {
  orders: number;
  sales: number;
  customers: number;
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  });

  if (!response.ok) {
    let message = `خطای سرور (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // Keep the status-based message when the response isn't JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function register(payload: {
  name: string;
  phone: string;
  password: string;
  restaurant_name: string;
}): Promise<AuthTokens> {
  return request<AuthTokens>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getDashboard(accessToken: string): Promise<DashboardData> {
  return request<DashboardData>('/api/dashboard', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export { API_BASE };
