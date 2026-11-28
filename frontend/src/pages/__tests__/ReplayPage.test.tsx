import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { fetchReplayEvents } from "../../api/risk";
import { mapReplayEventToHistoricalEvent } from "../../api/mappers";
import type { HistoricalEvent } from "../../types/replay";
import type { ReplayEventsResponse } from "../../api/risk";

vi.mock("../../api/risk", () => ({
  fetchReplayEvents: vi.fn(),
}));

vi.mock("../../api/mappers", () => ({
  mapReplayEventToHistoricalEvent: vi.fn(),
}));

const MOCK_LIVE_EVENT: HistoricalEvent = {
  id: "EVT-JHELUM-2014",
  title: "Jhelum Basin Flood Surge (Sample Reconstruction)",
  sector: "Anantnag - Sangam & Srinagar",
  hazard: "flood",
  dateRange: "2014-09-04 to 2014-09-07",
  provenance: "Historical Sample Reconstruction (CWC/IMD Archival Reference)",
  frames: [
    {
      id: "f1",
      timestamp: "2014-09-04 06:00 IST",
      phaseLabel: "T+00h • Onset",
      primaryMetricLabel: "Sangam Gauge",
      primaryMetricValue: "14.2 ft",
      secondaryMetricLabel: "6h Rainfall",
      secondaryMetricValue: "38 mm",
      alertTier: "Watch",
      summary: "Persistent monsoon trough over South Kashmir; soil saturation rising rapidly.",
    },
    {
      id: "f2",
      timestamp: "2014-09-04 18:00 IST",
      phaseLabel: "T+12h • Escalation",
      primaryMetricLabel: "Sangam Gauge",
      primaryMetricValue: "18.4 ft",
      secondaryMetricLabel: "6h Rainfall",
      secondaryMetricValue: "52 mm",
      alertTier: "Warning",
      summary: "Gauge breach imminent; evacuation of low-lying areas advised.",
    },
    {
      id: "f3",
      timestamp: "2014-09-05 06:00 IST",
      phaseLabel: "T+24h • Peak",
      primaryMetricLabel: "Sangam Gauge",
      primaryMetricValue: "22.1 ft",
      secondaryMetricLabel: "6h Rainfall",
      secondaryMetricValue: "71 mm",
      alertTier: "Emergency",
      summary: "Major flooding; Jhelum above danger mark at all stations.",
    },
    {
      id: "f4",
      timestamp: "2014-09-05 18:00 IST",
      phaseLabel: "T+36h • Recession",
      primaryMetricLabel: "Sangam Gauge",
      primaryMetricValue: "19.8 ft",
      secondaryMetricLabel: "6h Rainfall",
      secondaryMetricValue: "31 mm",
      alertTier: "Warning",
      summary: "Waters receding; search and rescue operations continue.",
    },
  ],
};

const MOCK_GULMARG_EVENT: HistoricalEvent = {
  id: "EVT-GULMARG-2024",
  title: "Gulmarg Avalanche Cycle (Sample Reconstruction)",
  sector: "Gulmarg - Affarwat Ridge",
  hazard: "avalanche",
  dateRange: "2024-02-10 to 2024-02-14",
  provenance: "Historical Sample Reconstruction (DGRE Archival Reference)",
  frames: [
    {
      id: "f1",
      timestamp: "2024-02-10 06:00 IST",
      phaseLabel: "T+00h • Onset",
      primaryMetricLabel: "Snow Depth",
      primaryMetricValue: "18 cm",
      secondaryMetricLabel: "Wind Speed",
      secondaryMetricValue: "45 km/h",
      alertTier: "Watch",
      summary: "Fresh snowfall accumulating on unstable layers.",
    },
    {
      id: "f2",
      timestamp: "2024-02-10 18:00 IST",
      phaseLabel: "T+12h • Escalation",
      primaryMetricLabel: "Snow Depth",
      primaryMetricValue: "32 cm",
      secondaryMetricLabel: "Wind Speed",
      secondaryMetricValue: "60 km/h",
      alertTier: "Warning",
      summary: "Rapid loading; avalanche danger rising.",
    },
  ],
};

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
    vi.clearAllMocks();
    vi.mocked(fetchReplayEvents).mockResolvedValue({
      total: 2,
      items: [
        {
          id: "EVT-JHELUM-2014",
          location_id: "JK-SGR-01",
          title: "Jhelum Basin Flood Surge (Sample Reconstruction)",
          sector: "Anantnag - Sangam & Srinagar",
          hazard: "flood",
          date_range: "2014-09-04 to 2014-09-07",
          provenance: "Historical Sample Reconstruction (CWC/IMD Archival Reference)",
          is_demo_fixture: true,
          frames: [
            {
              id: "f1",
              timestamp: "2014-09-04T06:00:00+05:30",
              phase_label: "T+00h • Onset",
              primary_metric_label: "Sangam Gauge",
              primary_metric_value: "14.2 ft",
              secondary_metric_label: "6h Rainfall",
              secondary_metric_value: "38 mm",
              alert_tier: "Watch",
              risk_class: "moderate",
              score: 0.45,
              confidence: 0.82,
              summary: "Persistent monsoon trough over South Kashmir.",
            },
            {
              id: "f2",
              timestamp: "2014-09-04T18:00:00+05:30",
              phase_label: "T+12h • Escalation",
              primary_metric_label: "Sangam Gauge",
              primary_metric_value: "18.4 ft",
              secondary_metric_label: "6h Rainfall",
              secondary_metric_value: "52 mm",
              alert_tier: "Warning",
              risk_class: "high",
              score: 0.72,
              confidence: 0.85,
              summary: "Gauge breach imminent; evacuation of low-lying areas advised.",
            },
            {
              id: "f3",
              timestamp: "2014-09-05T06:00:00+05:30",
              phase_label: "T+24h • Peak",
              primary_metric_label: "Sangam Gauge",
              primary_metric_value: "22.1 ft",
              secondary_metric_label: "6h Rainfall",
              secondary_metric_value: "71 mm",
              alert_tier: "Emergency",
              risk_class: "severe",
              score: 0.91,
              confidence: 0.88,
              summary: "Major flooding; Jhelum above danger mark at all stations.",
            },
            {
              id: "f4",
              timestamp: "2014-09-05T18:00:00+05:30",
              phase_label: "T+36h • Recession",
              primary_metric_label: "Sangam Gauge",
              primary_metric_value: "19.8 ft",
              secondary_metric_label: "6h Rainfall",
              secondary_metric_value: "31 mm",
              alert_tier: "Warning",
              risk_class: "high",
              score: 0.68,
              confidence: 0.80,
              summary: "Waters receding; search and rescue operations continue.",
            },
          ],
        },
        {
          id: "EVT-GULMARG-2024",
          location_id: "JK-GUL-01",
          title: "Gulmarg Avalanche Cycle (Sample Reconstruction)",
          sector: "Gulmarg - Affarwat Ridge",
          hazard: "avalanche",
          date_range: "2024-02-10 to 2024-02-14",
          provenance: "Historical Sample Reconstruction (DGRE Archival Reference)",
          is_demo_fixture: true,
          frames: [
            {
              id: "g1",
              timestamp: "2024-02-10T06:00:00+05:30",
              phase_label: "T+00h • Onset",
              primary_metric_label: "Snow Depth",
              primary_metric_value: "18 cm",
              secondary_metric_label: "Wind Speed",
              secondary_metric_value: "45 km/h",
              alert_tier: "Watch",
              risk_class: "moderate",
              score: 0.55,
              confidence: 0.78,
              summary: "Fresh snowfall accumulating on unstable layers.",
            },
            {
              id: "g2",
              timestamp: "2024-02-10T18:00:00+05:30",
              phase_label: "T+12h • Escalation",
              primary_metric_label: "Snow Depth",
              primary_metric_value: "32 cm",
              secondary_metric_label: "Wind Speed",
              secondary_metric_value: "60 km/h",
              alert_tier: "Warning",
              risk_class: "high",
              score: 0.82,
              confidence: 0.85,
              summary: "Rapid loading; avalanche danger rising.",
            },
          ],
        },
      ],
    } as ReplayEventsResponse);
    vi.mocked(mapReplayEventToHistoricalEvent).mockImplementation((event) => {
      if (event.id === "EVT-GULMARG-2024") return MOCK_GULMARG_EVENT;
      return MOCK_LIVE_EVENT;
    });

    localStorage.clear();
    localStorage.setItem("hima_rakshak_token", "test-jwt-token");
    localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
    window.history.pushState({}, "", "/replay");
  });

  it("renders initial historical event and steps forward/backward", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByRole("heading", { name: "Historical Event Replay" })).toBeInTheDocument();
    expect(await screen.findByText("14.2 ft")).toBeInTheDocument();
    expect(await screen.findByText("Frame 1 of 4")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /step forward/i }));
    expect(screen.getByText("18.4 ft")).toBeInTheDocument();
    expect(screen.getByText("Frame 2 of 4")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /step back/i }));
    expect(screen.getByText("14.2 ft")).toBeInTheDocument();
  });

  it("switches historical events and toggles loading and empty edge states", async () => {
    const user = userEvent.setup();
    render(<App />);

    const dropdown = await screen.findByLabelText("Select Historical Event");
    await user.selectOptions(dropdown, "EVT-GULMARG-2024");
    expect(await screen.findByText("18 cm")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Loading State" }));
    expect(screen.getByText(/Fetching live weather and river telemetry/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Empty / Zero-Threat" }));
    expect(screen.getByText(/No Active Threat Thresholds Exceeded/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /return to event replay/i }));
    expect(screen.getByLabelText("Timeline scrubber")).toBeInTheDocument();
  });
});
