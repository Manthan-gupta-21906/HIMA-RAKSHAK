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

describe("DashboardShell & OverviewPage", () => {
  beforeEach(() => {
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/");
  });

  it("renders header, sidebar navigation, KPIs, and priority sectors", () => {
    render(<App />);

    expect(screen.getByText("DDMA Control Room")).toBeInTheDocument();
    expect(screen.getByText("MG")).toBeInTheDocument();
    expect(screen.getByText("Regional Hazard Monitor")).toBeInTheDocument();
    expect(screen.getByText("Poonch - Surankote")).toBeInTheDocument();
    expect(screen.getByText("Gulmarg - Affarwat")).toBeInTheDocument();
    expect(screen.getByText("Kupwara - Machil")).toBeInTheDocument();
    expect(screen.getByText(/3h ago • stale/i)).toBeInTheDocument();
  });

  it("navigates across sidebar routes and toggles mobile drawer", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("link", { name: /field log/i }));
    expect(await screen.findByText("Field Observation Form")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /open navigation menu/i }));
    expect(screen.getByRole("navigation", { name: /mobile navigation/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /close navigation menu/i }));
    expect(screen.queryByRole("navigation", { name: /mobile navigation/i })).not.toBeInTheDocument();
  });
});
