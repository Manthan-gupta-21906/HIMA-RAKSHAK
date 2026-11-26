import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { evaluateLocationRisk } from "../../api/risk";

// Mock the observations API so form submission succeeds without a live backend.
vi.mock("../../api/observations", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/observations")>();
  return {
    ...actual,
    fetchObservations: vi.fn().mockResolvedValue({
      total: 1,
      items: [
        {
          observation_id: "obs-test-persisted-1",
          location_id: "JK-GUL-01",
          source_id: "src-field-obs",
          observed_at: new Date().toISOString(),
          metric: "snow_depth_cm",
          value: 48.0,
          unit: "cm",
          is_demo_fixture: false,
        },
      ],
      pagination: { total: 1, page: 1, page_size: 5, has_next: false },
    }),
    submitObservation: vi.fn().mockResolvedValue({
      observation_id: "obs-test-mock",
      location_id: "JK-GUL-01",
      source_id: "src-field-obs",
      observed_at: new Date().toISOString(),
      metric: "snow_depth_cm",
      value: 48.0,
      unit: "cm",
      is_demo_fixture: false,
    }),
  };
});

vi.mock("../../api/risk", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/risk")>();
  return {
    ...actual,
    evaluateLocationRisk: vi.fn().mockResolvedValue({
      location_id: "JK-GUL-01",
      risk_state: {
        location_id: "JK-GUL-01",
        updated_at: new Date().toISOString(),
        highest_risk_class: "moderate",
      },
      exposure: {
        location_id: "JK-GUL-01",
        population_exposed: 1200,
        roads_exposed_km: 4.5,
        critical_facilities_count: 1,
        coverage_status: "supported",
      },
      priority: {
        location_id: "JK-GUL-01",
        priority_level: "MEDIUM",
        priority_score: 0.42,
        hazard_risk_class: "moderate",
        prediction_status: "indicative",
        explanation: [],
      },
      alert: null,
    }),
  };
});

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

describe("FieldObservationPage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders FORM OPS-JK-449 with sector, hazard toggle, and dynamic metric input", () => {
    seedSession("/field-log");
    render(<App />);

    expect(screen.getByText(/form ops-jk-449/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /log field observation/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/target sector/i)).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /snowpack & avalanche/i })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /riverine basin \/ flood/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/fresh snow accumulation/i)).toBeInTheDocument();
    expect(screen.getByText("cm snow")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /risk state/i })).toBeInTheDocument();
  });

  it("switches metric label, unit, and range when toggling between avalanche and flood", async () => {
    const user = userEvent.setup();
    seedSession("/field-log");
    render(<App />);

    expect(screen.getByLabelText(/fresh snow accumulation/i)).toBeInTheDocument();
    expect(screen.getByText("cm snow")).toBeInTheDocument();
    expect(screen.getByText(/0\.0 cm snow – 350\.0 cm snow/)).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /riverine basin \/ flood/i }));
    expect(screen.getByLabelText(/river gauge depth/i)).toBeInTheDocument();
    expect(screen.getByText("ft water")).toBeInTheDocument();
    expect(screen.getByText(/0\.0 ft water – 50\.0 ft water/)).toBeInTheDocument();
  });

  it("shows E-401 validation error for negative value and clears on valid input", async () => {
    const user = userEvent.setup();
    seedSession("/field-log");
    render(<App />);

    const input = screen.getByLabelText(/fresh snow accumulation/i);
    await user.clear(input);
    await user.type(input, "-12.5");

    expect(screen.getByText(/validation error \(e-401\)/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid positive measurement/i)).toBeInTheDocument();

    await user.clear(input);
    await user.type(input, "48.0");
    expect(screen.queryByText(/validation error/i)).not.toBeInTheDocument();
  });

  it("transitions to success state on valid submission", async () => {
    const user = userEvent.setup();
    seedSession("/field-log?sector=JK-GUL-01&hazard=avalanche");
    render(<App />);

    const input = screen.getByLabelText(/fresh snow accumulation/i);
    await user.clear(input);
    await user.type(input, "48.0");

    await user.click(screen.getByRole("button", { name: /risk state/i }));

    await screen.findByText(/48\.0 cm snow/i);
    expect(screen.getByRole("heading", { name: /observation recorded/i })).toBeInTheDocument();
    expect(screen.getByText(/48\.0 cm snow/i)).toBeInTheDocument();
    expect(evaluateLocationRisk).toHaveBeenCalledWith("JK-GUL-01");
    expect(screen.getByText(/hazard risk recalculated \(moderate, priority: MEDIUM\)/i)).toBeInTheDocument();
  });

  it("reports unsupported prediction honestly when evaluation remains unsupported", async () => {
    vi.mocked(evaluateLocationRisk).mockResolvedValueOnce({
      location_id: "JK-GUL-01",
      risk_state: {
        location_id: "JK-GUL-01",
        updated_at: new Date().toISOString(),
        highest_risk_class: "unsupported",
      },
      exposure: {
        location_id: "JK-GUL-01",
        population_exposed: 0,
        roads_exposed_km: 0,
        critical_facilities_count: 0,
        coverage_status: "supported",
      },
      priority: {
        location_id: "JK-GUL-01",
        priority_level: "LOW",
        priority_score: 0.0,
        hazard_risk_class: "unsupported",
        prediction_status: "unsupported",
        explanation: [],
      },
      alert: null,
    });

    const user = userEvent.setup();
    seedSession("/field-log?sector=JK-GUL-01&hazard=avalanche");
    render(<App />);

    const input = screen.getByLabelText(/fresh snow accumulation/i);
    await user.clear(input);
    await user.type(input, "48.0");
    await user.click(screen.getByRole("button", { name: /risk state/i }));

    await screen.findByText(/prediction remains unsupported/i);
  });

  it("rejects out-of-range values", async () => {
    const user = userEvent.setup();
    seedSession("/field-log");
    render(<App />);

    await user.click(screen.getByRole("radio", { name: /riverine basin \/ flood/i }));
    const input = screen.getByLabelText(/river gauge depth/i);
    await user.clear(input);
    await user.type(input, "60.0");

    expect(screen.getByText(/enter a valid positive measurement/i)).toBeInTheDocument();
  });
});
