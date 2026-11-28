import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { fetchLocationDetail } from "../../api/locations";
import {
  fetchLocationExposure,
  fetchLocationPriority,
  fetchLocationRiskState,
} from "../../api/risk";

vi.mock("../../api/locations", () => ({
  fetchLocations: vi.fn(),
  fetchLocationDetail: vi.fn(),
}));

vi.mock("../../api/risk", () => ({
  fetchLocationRiskState: vi.fn(),
  fetchLocationExposure: vi.fn(),
  fetchLocationPriority: vi.fn(),
  evaluateLocationRisk: vi.fn(),
}));

const SEEDED_USER = {
  id: "usr-ddma-01",
  name: "M. Gupta",
  email: "ops.srinagar@jk-ddma.gov.in",
  initials: "MG",
  role: "district_operator",
  station: "DDMA Control Room",
  district: "Srinagar",
};

const LOCATION = {
  location_id: "JK-GUL-01",
  name: "Gulmarg — Affarwat Ridge",
  admin_unit: "Baramulla District, J&K",
  latitude: 34.0484,
  longitude: 74.3805,
  supported_hazards: ["avalanche"],
  coverage_status: "partial" as const,
  coverage_note: "Pilot avalanche corridor",
  is_demo_fixture: true,
  provenance: "official:dgre-pilot",
};

const RISK_STATE = {
  location_id: "JK-GUL-01",
  updated_at: "2026-11-29T00:00:00Z",
  flood: null,
  avalanche: null,
  primary_hazard: null,
  highest_risk_class: "high" as const,
};

const EXPOSURE = {
  location_id: "JK-GUL-01",
  evaluated_at: "2026-11-29T00:00:00Z",
  coverage_status: "partial" as const,
  population_exposed: 1850,
  settlements_count: 4,
  homes_exposed: 320,
  roads_exposed_km: 12.4,
  critical_facilities_count: 2,
  assets: [
    {
      asset_id: "asset-phc-1",
      asset_type: "critical_facility",
      name: "Gulmarg PHC",
      count: 1,
      count_type: "verified" as const,
      population_affected: 0,
      is_critical: true,
      metadata: {},
    },
    {
      asset_id: "asset-road-1",
      asset_type: "road",
      name: "Gondola Access Road",
      count: 1,
      count_type: "estimated" as const,
      population_affected: 0,
      is_critical: false,
      metadata: {},
    },
  ],
  missing_layers: ["power_grid"],
};

const PRIORITY = {
  location_id: "JK-GUL-01",
  evaluated_at: "2026-11-29T00:00:00Z",
  hazard_score: 0.9,
  hazard_risk_class: "high" as const,
  exposure_score: 0.6,
  impact_score: 0.7,
  priority_score: 0.81,
  coverage_status: "partial" as const,
  priority_level: "HIGH",
  confidence: 0.8,
  freshness: "fresh" as const,
  prediction_status: "ready" as const,
  weights_used: {},
  breakdown: {},
  explanation: [
    "Avalanche risk class is high",
    "Population exposure is elevated",
  ],
};

function seedSession() {
  localStorage.clear();
  localStorage.setItem("hima_rakshak_token", "test-jwt-token");
  localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
  window.history.pushState({}, "", "/locations/JK-GUL-01");
}

describe("LocationDetailPage live exposure and priority", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchLocationDetail).mockResolvedValue(LOCATION);
    vi.mocked(fetchLocationRiskState).mockResolvedValue(RISK_STATE);
    vi.mocked(fetchLocationExposure).mockResolvedValue(EXPOSURE);
    vi.mocked(fetchLocationPriority).mockResolvedValue(PRIORITY);
  });

  it("renders backend exposure and priority values when available", async () => {
    seedSession();
    render(<App />);

    expect(await screen.findByText("1850")).toBeInTheDocument();
    expect(screen.getByText("12.4 km")).toBeInTheDocument();
    expect(screen.getAllByText(/Gulmarg PHC/).length).toBeGreaterThan(0);
    expect(screen.getByText(/missing layers: power_grid/i)).toBeInTheDocument();

    expect(screen.getByText("Why This Priority")).toBeInTheDocument();
    expect(screen.getByText("Avalanche risk class is high")).toBeInTheDocument();
    expect(screen.getByText("Score 81%")).toBeInTheDocument();
    expect(screen.getAllByText("Live Backend").length).toBeGreaterThanOrEqual(2);
  });

  it("renders live risk-state hazard cards without blending pathways", async () => {
    vi.mocked(fetchLocationRiskState).mockResolvedValueOnce({
      ...RISK_STATE,
      flood: {
        risk_id: "risk-flood-live",
        location_id: "JK-GUL-01",
        hazard_type: "flood",
        risk_class: "low",
        score: 0.24,
        confidence: 0.7,
        lead_time_hours: 12,
        freshness: "fresh",
        prediction_status: "ready",
        readiness_reason: null,
        assessed_at: "2026-11-29T00:00:00Z",
        model_version: "flood-baseline-v1",
        provenance: {
          source_id: "src-cwc-01",
          source_name: "CWC",
          licence: "GODL",
          is_demo_fixture: true,
          ingested_at: "2026-11-29T00:05:00Z",
        },
      },
      avalanche: {
        risk_id: "risk-avalanche-live",
        location_id: "JK-GUL-01",
        hazard_type: "avalanche",
        risk_class: "severe",
        score: 0.95,
        confidence: 0.9,
        lead_time_hours: 24,
        freshness: "fresh",
        prediction_status: "ready",
        readiness_reason: null,
        assessed_at: "2026-11-29T00:00:00Z",
        model_version: "dgre-avalanche-v1",
        provenance: {
          source_id: "src-dgre-01",
          source_name: "DGRE",
          licence: "GODL",
          is_demo_fixture: true,
          ingested_at: "2026-11-29T00:05:00Z",
        },
      },
      primary_hazard: "avalanche",
      highest_risk_class: "severe",
    });

    seedSession();
    render(<App />);

    expect(await screen.findByText("Severe")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
    expect(screen.getByText("Live Risk State")).toBeInTheDocument();
    expect(screen.queryByText("Stage 3 Warning")).not.toBeInTheDocument();
    expect(screen.queryByText("Normal Range")).not.toBeInTheDocument();
  });

  it("shows explicit unavailable states instead of faking live exposure or priority", async () => {
    vi.mocked(fetchLocationExposure).mockRejectedValueOnce(new Error("exposure offline"));
    vi.mocked(fetchLocationPriority).mockRejectedValueOnce(new Error("priority offline"));
    seedSession();
    render(<App />);

    expect(
      await screen.findByText(/Live exposure unavailable: exposure offline/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Live priority assessment unavailable: priority offline/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Sample Catalogue")).toBeInTheDocument();
  });
});
