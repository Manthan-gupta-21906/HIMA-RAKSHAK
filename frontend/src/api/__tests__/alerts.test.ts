import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  acknowledgeAlert,
  fetchAlerts,
  updateAlertAction,
} from "../alerts";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("alerts API client", () => {
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

  it("serialises status, hazard, and location filters for GET /alerts", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ total: 0, items: [] }));
    globalThis.fetch = fetchMock;

    const response = await fetchAlerts({
      location_id: "JK-SGR-01",
      status: "active",
      hazard_type: "flood",
    });

    expect(response.total).toBe(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain(
      "/alerts?location_id=JK-SGR-01&status=active&hazard_type=flood"
    );
    expect(init.method).toBeUndefined();
  });

  it("posts an acknowledgement with an optional note", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ alert_id: "alert-flood-1" }));
    globalThis.fetch = fetchMock;

    await acknowledgeAlert("alert-flood-1", "Gauge watch activated");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/alerts/alert-flood-1/acknowledge");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ note: "Gauge watch activated" }));
  });

  it("patches action status and note", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ alert_id: "alert-flood-1" }));
    globalThis.fetch = fetchMock;

    await updateAlertAction("alert-flood-1", "resolved", "Road reopened");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/alerts/alert-flood-1/action");
    expect(init.method).toBe("PATCH");
    expect(init.body).toBe(
      JSON.stringify({ status: "resolved", action_note: "Road reopened" })
    );
  });
});
