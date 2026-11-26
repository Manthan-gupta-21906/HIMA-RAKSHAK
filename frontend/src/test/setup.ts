import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";

const originalFetch = globalThis.fetch;

beforeEach(() => {
  // Isolate unit tests from any live backend server running on port 8000
  globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network connection failed in test sandbox"));
});

afterEach(() => {
  globalThis.fetch = originalFetch;
});
