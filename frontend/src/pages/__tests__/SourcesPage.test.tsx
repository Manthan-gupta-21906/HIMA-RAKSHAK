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

describe("SourcesPage", () => {
  beforeEach(() => {
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/sources");
  });

  it("renders summary counts and all registered data sources", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Data Source Status" })).toBeInTheDocument();
    expect(screen.getByText("6 Sources")).toBeInTheDocument();
    expect(screen.getByText("4 Nominal")).toBeInTheDocument();
    expect(screen.getByText("1 High Latency")).toBeInTheDocument();
    expect(screen.getByText("1 Stale")).toBeInTheDocument();
    expect(screen.getByText("DGRE Kupwara-Machil Ultrasonic Probe")).toBeInTheDocument();
  });

  it("filters by status and agency, and updates timestamp on refresh", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "offline" }));
    expect(screen.getByText("DGRE Kupwara-Machil Ultrasonic Probe")).toBeInTheDocument();
    expect(screen.queryByText("IMD Srinagar Doppler Weather Radar")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "All Statuses" }));
    await user.selectOptions(screen.getByLabelText("Filter by agency"), "CWC");
    expect(screen.getByText("CWC Poonch-Surankote River Gauge")).toBeInTheDocument();
    expect(screen.queryByText("IMD Srinagar Doppler Weather Radar")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /refresh status/i }));
    expect(screen.getByText(/Checked at \d{2}:\d{2}/)).toBeInTheDocument();
  });
});
