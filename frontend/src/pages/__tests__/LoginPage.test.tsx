import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";

describe("LoginPage, roles, and protected routes", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
    window.history.pushState({}, "", "/login");
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("shows validation errors when submitting empty credentials", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText(/username or official email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it("validates username length and minimum password length", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/username or email/i), "ab");
    await user.type(screen.getByLabelText(/^password$/i), "123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText(/enter a valid username or email/i)).toBeInTheDocument();
    expect(screen.getByText(/at least 6 characters/i)).toBeInTheDocument();
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    render(<App />);

    const passwordInput = screen.getByLabelText(/^password$/i) as HTMLInputElement;
    expect(passwordInput.type).toBe("password");

    await user.click(screen.getByRole("button", { name: /show password/i }));
    expect(passwordInput.type).toBe("text");
  });

  it("redirects unauthenticated users from protected routes to login", async () => {
    localStorage.setItem(
      "hima_rakshak_auth_user",
      JSON.stringify({
        id: "usr-spoof",
        name: "Spoof",
        email: "spoof@example.com",
        initials: "SP",
        role: "admin",
        station: "Fake",
        district: "Fake",
      })
    );
    window.history.pushState({}, "", "/field-log");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /^sign in$/i })).toBeInTheDocument();
  });

  it("rejects login when backend is unreachable instead of falling back offline", async () => {
    const user = userEvent.setup();
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Failed to fetch"));
    render(<App />);

    await user.type(screen.getByLabelText(/username or email/i), "operator");
    await user.type(screen.getByLabelText(/^password$/i), "test-pass-123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/network connection failed/i);
    expect(localStorage.getItem("hima_rakshak_token")).toBeNull();
  });

  it("logs in via backend JWT API, uses server-verified role, and signs out", async () => {
    const user = userEvent.setup();
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/login")) {
        return new Response(
          JSON.stringify({ access_token: "jwt-admin-token", token_type: "bearer" }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({ username: "admin-user", role: "admin" }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      return new Response(JSON.stringify({ total: 0, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    render(<App />);

    await user.type(screen.getByLabelText(/username or email/i), "admin-user");
    await user.type(screen.getByLabelText(/^password$/i), "test-pass-123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/regional hazard monitor/i)).toBeInTheDocument();
    expect(localStorage.getItem("hima_rakshak_token")).toBe("jwt-admin-token");
    expect(screen.getByText(/sdma command center/i)).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /open profile and settings/i }));
    expect(screen.getByText("admin")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /sign out of session/i }));
    expect(await screen.findByRole("heading", { name: /^sign in$/i })).toBeInTheDocument();
    expect(localStorage.getItem("hima_rakshak_token")).toBeNull();
  });

  it("restricts viewer role from operator-only routes and hides Field Log nav", async () => {
    localStorage.setItem("hima_rakshak_token", "jwt-viewer-token");
    localStorage.setItem(
      "hima_rakshak_auth_user",
      JSON.stringify({
        id: "usr-sdma-09",
        name: "viewer",
        email: "viewer@sdma.gov.in",
        initials: "VI",
        role: "viewer",
        station: "J&K SDMA Advisory Desk",
        district: "Jammu",
      })
    );
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/me")) {
        return new Response(JSON.stringify({ username: "viewer", role: "viewer" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ total: 0, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    window.history.pushState({}, "", "/field-log");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /access restricted/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /field log/i })).not.toBeInTheDocument();
  });
});
