import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "../../App";

const SEEDED_USER = {
  id: "usr-ddma-01",
  name: "M. Gupta",
  email: "ops.srinagar@jk-ddma.gov.in",
  initials: "MG",
  role: "district_operator",
  station: "DDMA Control Room",
  district: "Srinagar",
};

describe("ProfilePage", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("hima_rakshak_token", "test-jwt-token");
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/profile");
  });

  it("renders operator account details and persists updated preferences", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByRole("heading", { name: "Profile & Settings" })).toBeInTheDocument();
    expect(screen.getByText("M. Gupta")).toBeInTheDocument();
    expect(screen.getByText("ops.srinagar@jk-ddma.gov.in")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Measurement Units"), "imperial");
    await user.selectOptions(screen.getByLabelText("Default Map Layer"), "terrain");
    await user.click(screen.getByRole("button", { name: /save preferences/i }));

    expect(await screen.findByText(/preferences saved for this workstation/i)).toBeInTheDocument();
    const stored = JSON.parse(localStorage.getItem("hima_rakshak_preferences") ?? "{}");
    expect(stored.unitSystem).toBe("imperial");
    expect(stored.defaultMapLayer).toBe("terrain");
  });

  it("resets defaults and signs out from profile page", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.selectOptions(screen.getByLabelText("Measurement Units"), "imperial");
    await user.click(screen.getByRole("button", { name: /reset defaults/i }));
    expect((screen.getByLabelText("Measurement Units") as HTMLSelectElement).value).toBe("metric");

    await user.click(screen.getByRole("button", { name: /sign out of session/i }));
    expect(await screen.findByRole("heading", { name: /^sign in$/i })).toBeInTheDocument();
  });
});
