import { fireEvent, render, screen, within, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { createLocation, updateLocationCoverage } from "../../api/locations";
import { registerSource, refreshSource } from "../../api/sources";

vi.mock("../../api/locations", () => ({
  fetchLocations: vi.fn(),
  fetchLocationDetail: vi.fn(),
  createLocation: vi.fn(),
  updateLocationCoverage: vi.fn(),
}));

vi.mock("../../api/sources", () => ({
  fetchSources: vi.fn(),
  registerSource: vi.fn(),
  refreshSource: vi.fn(),
}));

const SEEDED_USER = {
  id: "usr-admin-01",
  name: "System Administrator",
  email: "admin@jk-ddma.gov.in",
  initials: "AD",
  role: "admin",
  station: "SDMA Command Center",
  district: "Srinagar",
};

function seedSession() {
  localStorage.clear();
  localStorage.setItem("hima_rakshak_token", "test-jwt-token");
  localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
  window.history.pushState({}, "", "/admin");
}

function sectionOf(headingText: RegExp) {
  return within(
    screen.getByRole("heading", { name: headingText }).closest("section")!
  );
}

describe("AdminPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(createLocation).mockResolvedValue({
      location_id: "JK-PAH-01",
      name: "Pahalgam — Lidder Valley",
      admin_unit: "Anantnag District, J&K",
      latitude: 34.0161,
      longitude: 75.3150,
      supported_hazards: ["flood"],
      coverage_status: "partial",
      coverage_note: "Added in test.",
      is_demo_fixture: true,
      provenance: "admin",
    });
    vi.mocked(updateLocationCoverage).mockResolvedValue({
      location_id: "JK-PAH-01",
      name: "Pahalgam — Lidder Valley",
      admin_unit: "Anantnag District, J&K",
      latitude: 34.0161,
      longitude: 75.3150,
      supported_hazards: ["flood"],
      coverage_status: "supported",
      coverage_note: "Upgraded with field telemetry station.",
      is_demo_fixture: true,
      provenance: "admin",
    });
    vi.mocked(registerSource).mockResolvedValue({
      source_id: "src-imd-aws",
      source_name: "IMD AWS Network",
      provider: "IMD",
      dataset: "hourly rainfall",
      source_type: "weather",
      access_mode: "live",
      licence: "GODL",
      reference_url: undefined,
      update_frequency_minutes: 60,
      trust_classification: "institutional",
      is_authoritative: true,
      is_demo_fixture: false,
      freshness: "fresh",
      last_fetched_at: "2026-11-29T00:00:00Z",
      created_at: "2026-11-29T00:00:00Z",
    });
    vi.mocked(refreshSource).mockResolvedValue({
      source_id: "src-imd-aws",
      source_name: "IMD AWS Network",
      provider: "IMD",
      dataset: "hourly rainfall",
      source_type: "weather",
      access_mode: "live",
      licence: "GODL",
      reference_url: undefined,
      update_frequency_minutes: 60,
      trust_classification: "institutional",
      is_authoritative: true,
      is_demo_fixture: false,
      freshness: "fresh",
      last_fetched_at: "2026-11-29T00:05:00Z",
      created_at: "2026-11-29T00:00:00Z",
    });
  });

  it("renders admin-only management sections", () => {
    seedSession();
    render(<App />);

    expect(
      screen.getByRole("heading", { name: /administration/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /register pilot location/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /update location coverage/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /register data source/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /record source fetch/i })
    ).toBeInTheDocument();
  });

  it("registers a location via POST /locations as admin", async () => {
    seedSession();
    render(<App />);

    const section = sectionOf(/register pilot location/i);

    fireEvent.change(section.getByLabelText(/location id/i), {
      target: { value: "JK-PAH-01" },
    });
    fireEvent.change(section.getByLabelText(/name/i), {
      target: { value: "Pahalgam — Lidder Valley" },
    });
    fireEvent.change(section.getByLabelText(/admin unit/i), {
      target: { value: "Anantnag District, J&K" },
    });
    fireEvent.change(section.getByLabelText(/latitude/i), {
      target: { value: "34.0161" },
    });
    fireEvent.change(section.getByLabelText(/longitude/i), {
      target: { value: "75.3150" },
    });

    fireEvent.submit(section.getByRole("button", { name: /register location/i })
      .closest("form")!);

    await waitFor(() => {
      expect(createLocation).toHaveBeenCalledWith(
        expect.objectContaining({ location_id: "JK-PAH-01" })
      );
    });
  });

  it("updates location coverage via PATCH /locations/{id}/coverage", async () => {
    seedSession();
    render(<App />);

    const section = sectionOf(/update location coverage/i);

    fireEvent.change(section.getByLabelText(/location id/i), {
      target: { value: "JK-PAH-01" },
    });
    fireEvent.change(section.getByLabelText(/coverage note/i), {
      target: { value: "Upgraded with field telemetry station." },
    });

    fireEvent.submit(section.getByRole("button", { name: /update coverage/i })
      .closest("form")!);

    await waitFor(() => {
      expect(updateLocationCoverage).toHaveBeenCalledWith(
        "JK-PAH-01",
        expect.objectContaining({ coverage_status: "supported" })
      );
    });
  });

  it("registers a source via POST /sources", async () => {
    seedSession();
    render(<App />);

    const section = sectionOf(/register data source/i);

    fireEvent.change(section.getByLabelText(/source id/i), {
      target: { value: "src-imd-aws" },
    });
    fireEvent.change(section.getByLabelText(/provider/i), {
      target: { value: "IMD" },
    });
    fireEvent.change(section.getByLabelText(/licence/i), {
      target: { value: "GODL" },
    });
    fireEvent.change(section.getByLabelText(/update cadence/i), {
      target: { value: "60" },
    });

    fireEvent.submit(
      section.getByRole("button", { name: /register source/i }).closest("form")!
    );

    await waitFor(() => {
      expect(registerSource).toHaveBeenCalledWith(
        expect.objectContaining({ source_id: "src-imd-aws" })
      );
    });
  });

  it("records a fetch via POST /sources/{id}/fetch", async () => {
    seedSession();
    render(<App />);

    const section = sectionOf(/record source fetch/i);

    fireEvent.change(section.getByLabelText(/source id/i), {
      target: { value: "src-imd-aws" },
    });

    fireEvent.submit(
      section.getByRole("button", { name: /record fetch/i }).closest("form")!
    );

    await waitFor(() => {
      expect(refreshSource).toHaveBeenCalledWith("src-imd-aws");
    });
  });

  it("shows an API error when location registration fails", async () => {
    vi.mocked(createLocation).mockRejectedValueOnce(
      new Error("Backend /locations API: conflict")
    );
    seedSession();
    render(<App />);

    const section = sectionOf(/register pilot location/i);

    fireEvent.change(section.getByLabelText(/location id/i), {
      target: { value: "JK-PAH-01" },
    });
    fireEvent.change(section.getByLabelText(/name/i), {
      target: { value: "Pahalgam — Lidder Valley" },
    });
    fireEvent.change(section.getByLabelText(/admin unit/i), {
      target: { value: "Anantnag District, J&K" },
    });
    fireEvent.change(section.getByLabelText(/latitude/i), {
      target: { value: "34.0161" },
    });
    fireEvent.change(section.getByLabelText(/longitude/i), {
      target: { value: "75.3150" },
    });

    fireEvent.submit(
      section
        .getByRole("button", { name: /register location/i })
        .closest("form")!
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/conflict/i);
    });
  });
});
