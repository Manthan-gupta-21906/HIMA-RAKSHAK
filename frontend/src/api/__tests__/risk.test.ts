import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchReplayEvents } from "../risk";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("fetchReplayEvents API client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("hima_rakshak_token", "test-jwt-token");
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    localStorage.clear();
  });

  it("serialises query params for GET /risk/replay", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ total: 0, items: [] }));
    globalThis.fetch = fetchMock;

    await fetchReplayEvents({
      location_id: "JK-SGR-01",
      hazard_type: "flood",
      since: "2026-11-20T00:00:00Z",
      limit: 25,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/risk/replay");
    expect(url).toContain("location_id=JK-SGR-01");
    expect(url).toContain("hazard_type=flood");
    expect(url).toContain("since=");
    expect(url).toContain("limit=25");
    expect(init.method).toBeUndefined();
  });

  it("parses replay events response", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse({
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
                  summary: "flood risk assessed at high level.",
                },
              ],
            },
          ],
        })
      );
    globalThis.fetch = fetchMock;

    const res = await fetchReplayEvents({ location_id: "JK-SGR-01" });

    expect(res.total).toBe(1);
    expect(res.items[0].id).toBe("replay-JK-SGR-01-flood");
    expect(res.items[0].hazard).toBe("flood");
    expect(res.items[0].frames[0].alert_tier).toBe("High Risk");
    expect(res.items[0].frames[0].score).toBe(0.85);
  });
});
