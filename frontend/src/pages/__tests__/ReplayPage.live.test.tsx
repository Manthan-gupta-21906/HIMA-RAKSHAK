import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { fetchReplayEvents } from "../../api/risk";
import { mapReplayEventToHistoricalEvent } from "../../api/mappers";
import type { ReplayEventsResponse } from "../../api/risk";
import type { HistoricalEvent } from "../../types/replay";

vi.mock("../../api/risk", () => ({
  fetchReplayEvents: vi.fn(),
}));

vi.mock("../../api/mappers", () => ({
  mapReplayEventToHistoricalEvent: vi.fn(),
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

const LIVE_EVENT: HistoricalEvent = {
  id: "replay-JK-SGR-01-flood",
  title: "Flood Risk History — JK-SGR-01",
  sector: "Srinagar District, J&K",
  hazard: "flood",
  dateRange: "2026-11-20 to 2026-11-26",
  provenance: "Persisted risk assessment history",
  frames: [
    {
      id: "f1",
      timestamp: "2026-11-20 12:00 UTC",
      phaseLabel: "T+0 • 2026-11-20 12:00 UTC",
      primaryMetricLabel: "Risk Score",
      primaryMetricValue: "85%",
      secondaryMetricLabel: "Confidence",
      secondaryMetricValue: "88%",
      alertTier: "High Risk",
      summary: "flood risk assessed at high level (88% confidence).",
    },
  ],
};

function seedSession() {
  localStorage.clear();
  localStorage.setItem("hima_rakshak_token", "test-jwt-token");
  localStorage.setItem("hima_rakshak_auth_user", JSON.stringify(SEEDED_USER));
  window.history.pushState({}, "", "/replay");
}

describe("ReplayPage live backend integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders live replay events from backend with Live Backend badge", async () => {
    vi.mocked(fetchReplayEvents).mockResolvedValue({
      total: 1,
      items: [
        {
          id: "replay-JK-SGR-01-flood",
          location_id: "JK-SGR-01",
          title: "Flood Risk History — JK-SGR-01",
          sector: "Srinagar District, J&K",
          hazard: "flood",
          date_range: "2026-11-20 to 2026-11-26",
          provenance: "Persisted risk assessment history",
          is_demo_fixture: true,
          frames: [
            {
              id: "f1",
              timestamp: "2026-11-20T12:00:00Z",
              phase_label: "T+0 • 2026-11-20 12:00 UTC",
              primary_metric_label: "Risk Score",
              primary_metric_value: "85%",
              secondary_metric_label: "Confidence",
              secondary_metric_value: "88%",
              alert_tier: "High Risk",
              risk_class: "high",
              score: 0.85,
              confidence: 0.88,
              summary: "flood risk assessed at high level (88% confidence).",
            },
          ],
        },
      ],
    } as ReplayEventsResponse);
    vi.mocked(mapReplayEventToHistoricalEvent).mockReturnValue(LIVE_EVENT);

    seedSession();
    render(<App />);

    expect(
      await screen.findByText("Live Backend History")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Flood Risk History — JK-SGR-01" })
    ).toBeInTheDocument();
    expect(screen.getByText(/Srinagar District, J&K/)).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(fetchReplayEvents).toHaveBeenCalledTimes(1);
  });

  it("falls back to sample reconstruction when backend API fails", async () => {
    vi.mocked(fetchReplayEvents).mockRejectedValueOnce(
      new Error("Network connection failed")
    );

    seedSession();
    render(<App />);

    expect(
      await screen.findByText("Sample Reconstruction")
    ).toBeInTheDocument();
    // Mock events should still render
    expect(
      screen.getByRole("heading", { name: /Jhelum Basin Flood Surge/i })
    ).toBeInTheDocument();
    expect(
      await screen.findByText(/Backend \/risk\/replay API unavailable/i)
    ).toBeInTheDocument();
  });

  it("shows empty state when backend has no records (not sample data)", async () => {
    vi.mocked(fetchReplayEvents).mockResolvedValue({
      total: 0,
      items: [],
    } as ReplayEventsResponse);

    seedSession();
    render(<App />);

    // Should show empty state, not sample reconstruction
    expect(
      await screen.findByText("No Backend Records")
    ).toBeInTheDocument();
    expect(
      await screen.findByText("No historical replay events are available from the backend.")
    ).toBeInTheDocument();
    // Sample data should NOT appear
    expect(
      screen.queryByRole("heading", { name: /Jhelum Basin Flood Surge/i })
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Sample Reconstruction")).not.toBeInTheDocument();
  });

  it("shows Not Live Telemetry badge to distinguish from live data", async () => {
    vi.mocked(fetchReplayEvents).mockResolvedValue({
      total: 1,
      items: [
        {
          id: "replay-JK-SGR-01-flood",
          location_id: "JK-SGR-01",
          title: "Flood Risk History — JK-SGR-01",
          sector: "Srinagar District, J&K",
          hazard: "flood",
          date_range: "2026-11-20 to 2026-11-26",
          provenance: "Persisted risk assessment history",
          is_demo_fixture: true,
          frames: [],
        },
      ],
    } as ReplayEventsResponse);

    seedSession();
    render(<App />);

    expect(
      await screen.findByText("Not Live Telemetry")
    ).toBeInTheDocument();
  });
});
