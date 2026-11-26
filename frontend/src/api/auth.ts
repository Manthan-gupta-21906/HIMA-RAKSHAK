import { apiClient, storeToken, clearToken } from "./client";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  username: string;
  role: "admin" | "district_operator" | "viewer";
}

export async function loginApi(username: string, password: string): Promise<TokenResponse> {
  const data = await apiClient<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  storeToken(data.access_token);
  return data;
}

export async function getMeApi(): Promise<CurrentUser> {
  return apiClient<CurrentUser>("/auth/me");
}

export function logoutApi(): void {
  clearToken();
}
