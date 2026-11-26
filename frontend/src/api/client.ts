/**
 * Centralized API client for HIMA-RAKSHAK.
 * Handles base URL configuration, Bearer token attachment, and unified error handling.
 */

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export const TOKEN_STORAGE_KEY = "hima_rakshak_token";
export const AUTH_EXPIRED_EVENT = "hima:auth-expired";

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY) ?? localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string, persist = true): void {
  if (persist) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export interface ApiErrorDetail {
  field?: string;
  code?: string;
  message: string;
}

export class ApiError extends Error {
  status: number;
  code: string;
  details: ApiErrorDetail[];

  constructor(status: number, message: string, code = "API_ERROR", details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (networkError) {
    throw new ApiError(
      0,
      `Network connection failed: ${(networkError as Error).message || "Could not reach backend service"}. Ensure backend is running.`,
      "NETWORK_ERROR"
    );
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    let errorCode = `HTTP_${response.status}`;
    let errorDetails: ApiErrorDetail[] = [];

    try {
      const errorJson = await response.json();
      if (errorJson.message) {
        errorMessage = errorJson.message;
      } else if (errorJson.detail) {
        if (typeof errorJson.detail === "string") {
          errorMessage = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetails = errorJson.detail.map((d: { loc?: string[]; msg?: string; type?: string }) => ({
            field: d.loc?.join("."),
            message: d.msg || "Invalid value",
            code: d.type,
          }));
          errorMessage = errorDetails.map((d) => d.message).join(", ");
        }
      }
      if (errorJson.error_code) {
        errorCode = errorJson.error_code;
      }
      if (Array.isArray(errorJson.details)) {
        errorDetails = errorJson.details;
      }
    } catch {
      // response is not JSON
    }

    if (response.status === 401) {
      clearToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
      }
    }

    throw new ApiError(response.status, errorMessage, errorCode, errorDetails);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
