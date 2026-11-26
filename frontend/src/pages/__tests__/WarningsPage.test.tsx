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

describe("WarningsPage", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("hima_rakshak_token", "test-jwt-token");
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/warnings");
  });

  it("renders authoritative read-only bulletins and detail panel", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Official Warnings" })).toBeInTheDocument();
    expect(screen.getByText("Read-Only Record")).toBeInTheDocument();
    expect(screen.getAllByText(/Flash Flood Watch — Poonch/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Stage-3 Avalanche Warning — Gulmarg/i)).toBeInTheDocument();
  });

  it("filters by agency and updates detail panel on selection", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "DGRE" }));
    expect(screen.queryByText(/Flash Flood Watch — Poonch/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/Stage-3 Avalanche Warning — Gulmarg/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "All Agencies" }));
    await user.click(screen.getByRole("button", { name: /Heavy Precipitation & Snowfall Advisory/i }));
    expect(screen.getByText(/IMD MC Srinagar Nowcast\/Bulletin/i)).toBeInTheDocument();
  });

  it("filters by severity and search query with empty state", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.selectOptions(screen.getByLabelText("Filter by severity"), "Red");
    expect(screen.getAllByText(/Flash Flood Watch — Poonch/i).length).toBeGreaterThan(0);

    await user.type(screen.getByLabelText("Search warnings"), "nonexistent-sector");
    expect(screen.getByText(/no official bulletins match/i)).toBeInTheDocument();
  });
});
