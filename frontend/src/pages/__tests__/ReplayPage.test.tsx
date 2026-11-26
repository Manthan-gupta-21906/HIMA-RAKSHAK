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

describe("ReplayPage", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("hima_rakshak_token", "test-jwt-token");
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/replay");
  });

  it("renders initial historical event and steps forward/backward", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByRole("heading", { name: "Historical Event Replay" })).toBeInTheDocument();
    expect(screen.getByText("14.2 ft")).toBeInTheDocument();
    expect(screen.getByText("Frame 1 of 4")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /step forward/i }));
    expect(screen.getByText("18.4 ft")).toBeInTheDocument();
    expect(screen.getByText("Frame 2 of 4")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /step back/i }));
    expect(screen.getByText("14.2 ft")).toBeInTheDocument();
  });

  it("switches historical events and toggles loading and empty edge states", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.selectOptions(screen.getByLabelText("Select Historical Event"), "EVT-GULMARG-2024");
    expect(screen.getByText("18 cm")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Loading State" }));
    expect(screen.getByText(/Fetching live weather and river telemetry/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Empty / Zero-Threat" }));
    expect(screen.getByText(/No Active Threat Thresholds Exceeded/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /return to event replay/i }));
    expect(screen.getByLabelText("Timeline scrubber")).toBeInTheDocument();
  });
});
