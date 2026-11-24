/** Minimal auth client for backend token exchange. */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(
  username: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new Error(`Login failed: ${res.status}`);
  }
  return res.json();
}

export function getStoredToken(): string | null {
  return sessionStorage.getItem("hima_token");
}

export function storeToken(token: string): void {
  sessionStorage.setItem("hima_token", token);
}

export function clearToken(): void {
  sessionStorage.removeItem("hima_token");
}
