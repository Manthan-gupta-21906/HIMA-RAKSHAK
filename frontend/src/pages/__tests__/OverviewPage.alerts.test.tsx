import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { fetchAlerts, type AlertRecord } from "../../api/alerts";
import { fetchLocations } from "../../api/locations";
import { fetchLocationRiskState } from "../../api/risk";

vi.mock("../../api/alerts", () => ({
  fetchAlerts: vi.fn(),
  acknowledgeAlert: vi.fn(),
  updateAlertAction: vi.fn(),
}));

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

function alertFixture(
  alertId: string,
  status: AlertRecord["status"]
): AlertRecord {
  return {
    alert_id: alertId,
    location_id: "JK-SGR-01",
    hazard_type: "flood",
    risk_id: "risk-flood-1",
    priority_level: "HIGH",
    priority_score: 0.8,
    title: "HIGH Flood Alert — JK-SGR-01",
    recommendation: "Activate river gauge watch.",
    explanation: ["River level above warning mark"],
    status,
    acknowledged_by: null,
    acknowledged_at: null,
    action_note: null,
    action_updated_at: null,
    is_official_warning: false,
    created_at: "2026-11-29T00:00:00Z",
  };
}

function seedSession() {
  localStorage.clear();
  localStorage.setItem("hima_rakshak_token", "test-jwt-token");
  localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
  window.history.pushState({}, "", "/");
}

describe("OverviewPage operational alert KPI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchLocations).mockResolvedValue({
      total: 1,
      items: [
        {
          location_id: "JK-SGR-01",
          name: "Srinagar — Jhelum Floodplain",
          admin_unit: "Srinagar District, J&K",
          latitude: 34.0837,
          longitude: 74.7973,
          supported_hazards: ["flood"],
          coverage_status: "supported",
          coverage_note: "Operational pilot gauge station",
          is_demo_fixture: true,
          provenance: "official:cwc-pilot",
        },
      ],
      pagination: { total: 1, page: 1, page_size: 20, has_next: false },
    });
    vi.mocked(fetchLocationRiskState).mockResolvedValue({
      location_id: "JK-SGR-01",
      updated_at: "2026-11-29T00:00:00Z",
      flood: null,
      avalanche: null,
      primary_hazard: null,
      highest_risk_class: "low",
    });
    vi.mocked(fetchAlerts).mockResolvedValue({
      total: 4,
      items: [
        alertFixture("alert-1", "active"),
        alertFixture("alert-2", "active"),
        alertFixture("alert-3", "acknowledged"),
        alertFixture("alert-4", "in_progress"),
      ],
    });
  });

  it("uses backend operational alert counts instead of inferred risk tiers", async () => {
    seedSession();
    render(<App />);

    expect(await screen.findByText("2 Active")).toBeInTheDocument();
    expect(
      screen.getByText("1 acknowledged • 1 in progress")
    ).toBeInTheDocument();
    expect(screen.queryByText("3 Sectors")).not.toBeInTheDocument();
  });

  it("shows an explicit unavailable KPI when the alert feed fails", async () => {
    vi.mocked(fetchAlerts).mockRejectedValueOnce(new Error("alerts offline"));
    seedSession();
    render(<App />);

    expect(
      await screen.findByText("Operational alert feed unavailable")
    ).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
