import { describe, expect, it } from "vitest";
import { mapLocationAndRiskToSector } from "../mappers";
import type { LocationOut } from "../locations";

const BASE_LOCATION: LocationOut = {
  location_id: "JK-DRS-01",
  name: "Drass — NH-1 Corridor",
  admin_unit: "Kargil District",
  latitude: 34.43,
  longitude: 75.75,
  supported_hazards: ["avalanche"],
  coverage_status: "supported",
  coverage_note: "Pilot corridor",
  is_demo_fixture: true,
  provenance: "demo_fixture",
};

describe("mapLocationAndRiskToSector", () => {
  it("defaults to Unsupported instead of Low when risk state is missing or unsupported", () => {
    const missingRisk = mapLocationAndRiskToSector(BASE_LOCATION, null);
    expect(missingRisk.riskTier).toBe("Unsupported");

    const unsupportedRisk = mapLocationAndRiskToSector(BASE_LOCATION, {
      location_id: "JK-DRS-01",
      updated_at: new Date().toISOString(),
      highest_risk_class: "unsupported",
      avalanche: null,
      flood: null,
      primary_hazard: null,
    });
    expect(unsupportedRisk.riskTier).toBe("Unsupported");
  });

  it("maps explicit low risk_class to Low", () => {
    const lowRisk = mapLocationAndRiskToSector(BASE_LOCATION, {
      location_id: "JK-DRS-01",
      updated_at: new Date().toISOString(),
      highest_risk_class: "low",
      avalanche: null,
      flood: null,
      primary_hazard: "avalanche",
    });
    expect(lowRisk.riskTier).toBe("Low");
  });
});
