// Determine API base URL robustly for both Docker and local dev.
// Prefer VITE_API_URL when provided; otherwise infer from the current hostname (port 8000).
const envBase = (import.meta as any).env?.VITE_API_URL as string | undefined;
const isDev = typeof window !== 'undefined' && window.location.port === '5173'
// In dev, prefer Vite proxy to remove CORS entirely
let API_BASE = isDev ? '/api' : undefined as unknown as string;
if (!API_BASE) {
  const inferred = (typeof window !== 'undefined')
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : 'http://localhost:8000';
  API_BASE = (envBase && envBase.replace(/\/$/, "")) || inferred;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options,
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      message = (data as any)?.detail || message;
    } catch {}
    throw new Error(message);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

export type LoginResponse = { access_token: string; token_type: string };

export const api = {
  post: request,
  login: (email: string, password: string) =>
    request<LoginResponse>(`/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (name: string, email: string, password: string, role: 'student'|'teacher'|'admin') =>
    request(`/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ name, email, password, role }),
    }),
  requestVerifyEmail: (email: string) =>
    request(`/auth/verify/request`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  confirmVerifyEmail: (token: string) =>
    request(`/auth/verify/confirm`, {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),
  forgotPassword: (email: string) =>
    request(`/auth/password/forgot`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, new_password: string) =>
    request(`/auth/password/reset`, {
      method: 'POST',
      body: JSON.stringify({ token, new_password }),
    }),
};
