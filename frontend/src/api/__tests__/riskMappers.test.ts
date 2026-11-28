import { describe, expect, it } from "vitest";
import type { RiskAssessmentContract } from "../risk";
import { mapRiskStateToHazardEngines } from "../riskMappers";

function assessment(
  overrides: Partial<RiskAssessmentContract> = {}
): RiskAssessmentContract {
  return {
    risk_id: "risk-test-1",
    location_id: "JK-GUL-01",
    hazard_type: "avalanche",
    risk_class: "high",
    score: 0.8,
    confidence: 0.85,
    lead_time_hours: 24,
    freshness: "fresh",
    prediction_status: "ready",
    readiness_reason: null,
    assessed_at: "2026-11-29T00:00:00Z",
    model_version: "model-v1",
    provenance: {
      source_id: "src-dgre-01",
      source_name: "DGRE",
      licence: "GODL",
      is_demo_fixture: true,
      ingested_at: "2026-11-29T00:05:00Z",
    },
    ...overrides,
  };
}

function state(
  flood: RiskAssessmentContract | null,
  avalanche: RiskAssessmentContract | null
) {
  return {
    location_id: "JK-GUL-01",
    updated_at: "2026-11-29T00:00:00Z",
    flood,
    avalanche,
    primary_hazard: null,
    highest_risk_class: "high" as const,
  };
}

describe("mapRiskStateToHazardEngines", () => {
  it("keeps flood and avalanche pathways independent", () => {
    const engines = mapRiskStateToHazardEngines(
      state(
        assessment({ hazard_type: "flood", risk_class: "low", score: 0.2 }),
        assessment({ hazard_type: "avalanche", risk_class: "severe", score: 0.95 })
      )
    );

    expect(engines.flood.statusLabel).toBe("Low");
    expect(engines.flood.status).toBe("normal");
    expect(engines.avalanche.statusLabel).toBe("Severe");
    expect(engines.avalanche.status).toBe("warning");
    expect(engines.avalanche.progress?.percent).toBeCloseTo(95);
    expect(engines.avalanche.title).toBe("DGRE Avalanche Model");
    expect(engines.flood.title).toBe("Hydrology & Runoff Engine");
  });

  it("renders an explicit no-assessment state when a pathway is missing", () => {
    const engines = mapRiskStateToHazardEngines(state(null, null));

    expect(engines.flood.available).toBe(false);
    expect(engines.flood.statusLabel).toBe("No Assessment");
    expect(engines.avalanche.available).toBe(false);
    expect(engines.avalanche.readiness).toBe("insufficient");
    expect(engines.avalanche.metrics).toHaveLength(0);
  });

  it("marks unsupported assessments as unavailable", () => {
    const engines = mapRiskStateToHazardEngines(
      state(
        assessment({
          hazard_type: "flood",
          risk_class: "unsupported",
          prediction_status: "unsupported",
          score: null,
        }),
        null
      )
    );

    expect(engines.flood.available).toBe(false);
    expect(engines.flood.status).toBe("insufficient");
    expect(engines.flood.statusLabel).toBe("Unsupported");
    expect(engines.flood.progress).toBeUndefined();
  });

  it("surfaces stale readiness without inventing a fresh assessment", () => {
    const engines = mapRiskStateToHazardEngines(
      state(
        null,
        assessment({
          hazard_type: "avalanche",
          freshness: "stale",
          prediction_status: "stale",
        })
      )
    );

    expect(engines.avalanche.readiness).toBe("insufficient");
    expect(engines.avalanche.readinessLabel).toBe("Stale assessment");
    expect(engines.avalanche.freshness).toBe("Stale");
    expect(engines.avalanche.note).toMatch(/stale/i);
  });
});
