import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/locations": "http://127.0.0.1:8000",
      "/risk": "http://127.0.0.1:8000",
      "/sources": "http://127.0.0.1:8000",
      "/warnings": "http://127.0.0.1:8000",
      "/observations": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
