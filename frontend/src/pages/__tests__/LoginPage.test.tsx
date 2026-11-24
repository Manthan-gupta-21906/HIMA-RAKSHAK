import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "../../App";

describe("LoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.pushState({}, "", "/login");
  });

  it("shows validation errors when submitting empty credentials", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText(/official email address is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it("validates email format and minimum password length", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/official email/i), "not-an-email");
    await user.type(screen.getByLabelText(/^password$/i), "123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText(/enter a valid email address/i)).toBeInTheDocument();
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

  it("logs in with demo credentials and signs out", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /use demo credentials/i }));
    await user.click(screen.getByRole("button", { name: /sdrf field officer/i }));
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/regional hazard monitor/i)).toBeInTheDocument();
    expect(screen.getByText(/sdrf ground unit 04/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /sign out/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /open profile and settings/i }));
    await user.click(screen.getByRole("button", { name: /sign out of session/i }));
    expect(await screen.findByRole("heading", { name: /^sign in$/i })).toBeInTheDocument();
  });
});
