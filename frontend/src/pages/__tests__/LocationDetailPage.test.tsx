import { render, screen } from "@testing-library/react";
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

function seedSession(path: string) {
  localStorage.setItem("hima_rakshak_token", "test-jwt-token");
  localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
  window.history.pushState({}, "", path);
}

describe("LocationDetailPage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders flood and avalanche as independent assessment cards", () => {
    seedSession("/locations/JK-GUL-01");
    render(<App />);

    expect(screen.getByRole("heading", { name: "Gulmarg - Affarwat Ridge" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "DGRE Avalanche Model" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hydrology & Runoff Engine" })).toBeInTheDocument();
    expect(screen.getByText("Stage 3 Warning")).toBeInTheDocument();
    expect(screen.getByText("Normal Range")).toBeInTheDocument();
    expect(screen.getAllByText(/high confidence/i)).toHaveLength(2);
    expect(screen.getByText("Exposure & Critical Assets")).toBeInTheDocument();
    expect(screen.getByText("Gulmarg Gondola upper terminal")).toBeInTheDocument();
    expect(screen.getByText("Sensor Network Status")).toBeInTheDocument();
    expect(screen.getByText("DGRE Stage-3 Avalanche Warning")).toBeInTheDocument();
  });

  it("shows the avalanche readiness gate when snowpack coverage is insufficient", () => {
    seedSession("/locations/JK-SGR-01");
    render(<App />);

    expect(screen.getByRole("heading", { name: "Poonch - Surankote Valley" })).toBeInTheDocument();
    expect(
      screen.getByText("Avalanche readiness: insufficient snowpack coverage")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/do not use this panel for avalanche decisions/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Insufficient Coverage")).toBeInTheDocument();
    expect(screen.getByText("Flood Warning")).toBeInTheDocument();
    expect(screen.queryByText("Avalanche telemetry operational")).not.toBeInTheDocument();
  });

  it("links each engine to the pre-filled field observation form", () => {
    seedSession("/locations/JK-GUL-01");
    render(<App />);

    expect(screen.getByRole("link", { name: /log observation/i })).toHaveAttribute(
      "href",
      "/field-log?sector=JK-GUL-01&hazard=avalanche"
    );
    expect(screen.getByRole("link", { name: /log gauge data/i })).toHaveAttribute(
      "href",
      "/field-log?sector=JK-GUL-01&hazard=flood"
    );
  });

  it("renders a recoverable not-found state for unknown sectors", () => {
    seedSession("/locations/JK-UNKNOWN");
    render(<App />);

    expect(screen.getByRole("heading", { name: "Sector not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /back to risk map/i })).toHaveAttribute("href", "/map");
  });
});
