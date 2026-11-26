import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  apiClient,
  ApiError,
  clearToken,
  getStoredToken,
  storeToken,
  TOKEN_STORAGE_KEY,
} from "../client";

describe("apiClient and Token Management", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  describe("Token storage", () => {
    it("stores and retrieves token in localStorage by default", () => {
      storeToken("test-jwt-token-123");
      expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBe("test-jwt-token-123");
      expect(getStoredToken()).toBe("test-jwt-token-123");
    });

    it("stores and retrieves token in sessionStorage when persist is false", () => {
      storeToken("session-token-456", false);
      expect(sessionStorage.getItem(TOKEN_STORAGE_KEY)).toBe("session-token-456");
      expect(getStoredToken()).toBe("session-token-456");
    });

    it("clears token from both storages", () => {
      storeToken("tok-1");
      clearToken();
      expect(getStoredToken()).toBeNull();
      expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
      expect(sessionStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
    });
  });

  describe("ApiError class", () => {
    it("creates instance with status, message, code and details", () => {
      const err = new ApiError(404, "Location not found", "NOT_FOUND", [
        { field: "location_id", message: "Unknown ID" },
      ]);
      expect(err.name).toBe("ApiError");
      expect(err.status).toBe(404);
      expect(err.message).toBe("Location not found");
      expect(err.code).toBe("NOT_FOUND");
      expect(err.details).toHaveLength(1);
      expect(err.details[0].field).toBe("location_id");
    });
  });

  describe("apiClient requests", () => {
    it("attaches Authorization header when token is stored", async () => {
      storeToken("my-bearer-token");

      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: "ok" }),
      });
      globalThis.fetch = mockFetch;

      const result = await apiClient<{ status: string }>("/test-endpoint");
      expect(result).toEqual({ status: "ok" });
      expect(mockFetch).toHaveBeenCalledTimes(1);

      const calledHeaders = mockFetch.mock.calls[0][1].headers as Headers;
      expect(calledHeaders.get("Authorization")).toBe("Bearer my-bearer-token");
    });

    it("clears token and throws ApiError on 401 response", async () => {
      storeToken("expired-token");

      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Token expired" }),
      });

      await expect(apiClient("/auth/me")).rejects.toThrow(ApiError);
      expect(getStoredToken()).toBeNull();
    });

    it("parses validation details on 422 Unprocessable Entity", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({
          detail: [
            { loc: ["body", "password"], msg: "String should have at least 4 characters", type: "string_too_short" },
          ],
        }),
      });

      try {
        await apiClient("/auth/login", { method: "POST" });
        expect.fail("Should have thrown ApiError");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const err = e as ApiError;
        expect(err.status).toBe(422);
        expect(err.details).toHaveLength(1);
        expect(err.details[0].field).toBe("body.password");
      }
    });

    it("throws NetworkError with status 0 on fetch failure", async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error("Failed to fetch"));

      try {
        await apiClient("/locations");
        expect.fail("Should have thrown ApiError");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        const err = e as ApiError;
        expect(err.status).toBe(0);
        expect(err.code).toBe("NETWORK_ERROR");
        expect(err.message).toContain("Network connection failed");
      }
    });
  });
});
