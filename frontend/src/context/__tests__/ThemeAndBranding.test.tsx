import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "../../App";

const SEEDED_USER = {
  id: "usr-ddma-01",
  name: "M. Gupta",
  email: "ops.srinagar@jk-ddma.gov.in",
  initials: "MG",
  role: "operator",
  station: "DDMA Control Room",
  district: "Srinagar",
};

describe("Theme & Branding (Phase 10)", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("renders custom HIMA-RAKSHAK logo and toggles dark mode on LoginPage", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/login");
    render(<App />);

    const logo = screen.getByAltText("HIMA-RAKSHAK Logo") as HTMLImageElement;
    expect(logo.getAttribute("src")).toBe("/hima-rakshak-logo.png");

    expect(document.documentElement.classList.contains("dark")).toBe(false);
    await user.click(screen.getByRole("button", { name: /switch to dark mode/i }));

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("hima_rakshak_theme")).toBe("dark");
  });

  it("renders custom logo in TopHeader and allows theme switching in ProfilePage", async () => {
    const user = userEvent.setup();
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/profile");
    render(<App />);

    const logo = screen.getByAltText("HIMA-RAKSHAK Logo") as HTMLImageElement;
    expect(logo.getAttribute("src")).toBe("/hima-rakshak-logo.png");

    await user.selectOptions(screen.getByLabelText("Display Theme"), "dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    await user.click(screen.getByRole("button", { name: /switch to light mode/i }));
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
