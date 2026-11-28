import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import {
  acknowledgeAlert,
  fetchAlerts,
  updateAlertAction,
  type AlertRecord,
} from "../../api/alerts";
import { fetchLocations } from "../../api/locations";

vi.mock("../../api/alerts", () => ({
  fetchAlerts: vi.fn(),
  acknowledgeAlert: vi.fn(),
  updateAlertAction: vi.fn(),
}));

vi.mock("../../api/locations", () => ({
  fetchLocations: vi.fn(),
  fetchLocationDetail: vi.fn(),
}));

const BASE_USER = {
  id: "usr-ddma-01",
  name: "M. Gupta",
  email: "ops.srinagar@jk-ddma.gov.in",
  initials: "MG",
  station: "DDMA Control Room",
  district: "Srinagar",
};

const ACTIVE_ALERT: AlertRecord = {
  alert_id: "alert-flood-abc123",
  location_id: "JK-SGR-01",
  hazard_type: "flood",
  risk_id: "risk-flood-1",
  priority_level: "HIGH",
  priority_score: 0.82,
  title: "HIGH Flood Alert — JK-SGR-01",
  recommendation:
    "Activate river gauge watch, inspect low-lying drainage/bridges, and pre-position SDRF flood response teams.",
  explanation: [
    "River level above the warning mark",
    "Population exposure is elevated",
  ],
  status: "active",
  acknowledged_by: null,
  acknowledged_at: null,
  action_note: null,
  action_updated_at: null,
  is_official_warning: false,
  created_at: "2026-11-28T10:00:00Z",
};

function seedSession(role: "admin" | "district_operator" | "viewer") {
  localStorage.clear();
  localStorage.setItem("hima_rakshak_token", "test-jwt-token");
  localStorage.setItem(
    "hima_rakshak_auth_user",
    JSON.stringify({ ...BASE_USER, role })
  );
  window.history.pushState({}, "", "/alerts");
}

describe("AlertsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchAlerts).mockResolvedValue({
      total: 1,
      items: [ACTIVE_ALERT],
    });
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
    vi.mocked(acknowledgeAlert).mockResolvedValue({
      ...ACTIVE_ALERT,
      status: "acknowledged",
      acknowledged_by: "M. Gupta",
      acknowledged_at: "2026-11-28T10:05:00Z",
    });
    vi.mocked(updateAlertAction).mockResolvedValue({
      ...ACTIVE_ALERT,
      status: "resolved",
      action_note: "Road reopened",
      action_updated_at: "2026-11-28T11:00:00Z",
    });
  });

  it("renders backend alerts with recommendation, explanation, and location name", async () => {
    seedSession("district_operator");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Operational Alerts" })
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: "HIGH Flood Alert — JK-SGR-01" })
    ).toHaveLength(2);
    expect(screen.getAllByText(/Activate river gauge watch/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText("River level above the warning mark")
    ).toBeInTheDocument();
    expect(screen.getAllByText("Srinagar — Jhelum Floodplain").length).toBeGreaterThan(0);
    expect(screen.getByText("Not Official Warnings")).toBeInTheDocument();
  });

  it("keeps viewers read-only", async () => {
    seedSession("viewer");
    render(<App />);

    await screen.findByRole("heading", { name: "Operational Alerts" });
    expect(
      screen.getByText(/Read-only: operator or administrator role required/i)
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /acknowledge alert/i })
    ).not.toBeInTheDocument();
  });

  it("lets an operator acknowledge and update action status", async () => {
    const user = userEvent.setup();
    seedSession("district_operator");
    render(<App />);

    await screen.findByRole("heading", { name: "Operational Alerts" });

    await user.type(
      screen.getByLabelText(/acknowledge note/i),
      "Gauge watch activated"
    );
    await user.click(screen.getByRole("button", { name: /acknowledge alert/i }));

    await waitFor(() =>
      expect(acknowledgeAlert).toHaveBeenCalledWith(
        "alert-flood-abc123",
        "Gauge watch activated"
      )
    );

    await user.selectOptions(screen.getByLabelText(/action status/i), "resolved");
    await user.type(screen.getByLabelText(/action note/i), "Road reopened");
    await user.click(
      screen.getByRole("button", { name: /save action update/i })
    );

    await waitFor(() =>
      expect(updateAlertAction).toHaveBeenCalledWith(
        "alert-flood-abc123",
        "resolved",
        "Road reopened"
      )
    );
  });

  it("shows an explicit unavailable state when the alert feed fails", async () => {
    vi.mocked(fetchAlerts).mockRejectedValueOnce(
      new Error("Network connection failed")
    );
    seedSession("district_operator");
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Backend \/alerts API unavailable/i
    );
    expect(screen.getByText(/No alerts can be displayed/i)).toBeInTheDocument();
  });
});
