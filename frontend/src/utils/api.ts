const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

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
