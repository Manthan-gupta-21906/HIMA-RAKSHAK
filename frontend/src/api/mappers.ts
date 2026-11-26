import type { MonitoringSector, HazardPathway, RiskTier } from "../data/mockSectors";
import type { DataSourceRecord, SourceAgency, SourceStatus } from "../types/dataSource";
import type { OfficialWarning, WarningAgency, WarningHazard, WarningSeverity } from "../types/warning";
import type { LocationOut } from "./locations";
import type { LocationRiskState, RiskAssessmentContract } from "./risk";
import type { SourceOut } from "./sources";
import type { OfficialWarningContract } from "./warnings";

export function mapLocationAndRiskToSector(
  loc: LocationOut,
  riskState?: LocationRiskState | null
): MonitoringSector {
  const hazardType: HazardPathway =
    loc.supported_hazards.includes("avalanche") && !loc.supported_hazards.includes("flood")
      ? "avalanche"
      : "flood";

  // Check hazard-specific assessment or fallback to available hazard
  const assessment: RiskAssessmentContract | undefined =
    hazardType === "avalanche"
      ? (riskState?.avalanche || riskState?.flood || undefined)
      : (riskState?.flood || riskState?.avalanche || undefined);

  let riskTier: RiskTier = "Low";
  const riskClass = (assessment?.risk_class || riskState?.highest_risk_class || "").toLowerCase();
  if (riskClass === "severe" || riskClass === "high") {
    riskTier = hazardType === "avalanche" ? "Stage 3" : "High Risk";
  } else if (riskClass === "moderate") {
    riskTier = "Moderate";
  }

  let confidence: "High" | "Moderate" | "Low" = "Moderate";
  if (assessment?.confidence !== undefined) {
    if (assessment.confidence >= 0.75) confidence = "High";
    else if (assessment.confidence <= 0.4) confidence = "Low";
  }

  const isStale =
    assessment?.freshness === "stale" ||
    assessment?.prediction_status === "stale" ||
    loc.coverage_status !== "supported";

  const coordinates = loc.geometry_geojson?.coordinates as [number, number] | undefined;

  return {
    id: loc.location_id,
    name: loc.name,
    district: loc.admin_unit,
    elevationM: coordinates ? 1800 : 2000,
    lat: loc.latitude,
    lng: loc.longitude,
    hazard: hazardType,
    threatLabel: assessment?.readiness_reason || loc.coverage_note || `${loc.name} multi-hazard status`,
    riskTier,
    summaryMetric:
      assessment?.score !== undefined && assessment.score !== null
        ? `Score: ${(assessment.score * 100).toFixed(0)}% (${assessment.risk_class})`
        : `Coverage: ${loc.coverage_status}`,
    exposureSummary: loc.coverage_note || `${loc.admin_unit} basin exposure monitoring active`,
    confidence,
    updatedAgo: assessment?.assessed_at
      ? new Date(assessment.assessed_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "Live API",
    isStale,
    isPriority: riskClass === "severe" || riskClass === "high",
  };
}

export function mapSourceOutToRecord(src: SourceOut): DataSourceRecord {
  let agency: SourceAgency = "SDRF";
  const nameUpper = (src.source_name || src.provider || "").toUpperCase();
  if (nameUpper.includes("IMD")) agency = "IMD";
  else if (nameUpper.includes("CWC")) agency = "CWC";
  else if (nameUpper.includes("DGRE")) agency = "DGRE";

  let status: SourceStatus = "online";
  if (src.freshness === "stale") {
    status = "offline";
  } else if (src.freshness === "unknown") {
    status = "delayed";
  }

  return {
    id: src.source_id,
    name: src.source_name || `${src.provider} - ${src.dataset}`,
    agency,
    category: src.source_type,
    coverage: src.access_mode.toUpperCase(),
    status,
    latencyLabel: `${src.update_frequency_minutes} min cadence`,
    lastUpdated: src.last_fetched_at
      ? new Date(src.last_fetched_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "Not fetched yet",
    cadence: `Every ${src.update_frequency_minutes} mins`,
    provenanceNote: `Licence: ${src.licence} • Trust: ${src.trust_classification}`,
    knownLimitation: src.is_demo_fixture ? "Demo Fixture (Test Registry)" : undefined,
  };
}

export function mapWarningContractToOfficialWarning(warn: OfficialWarningContract): OfficialWarning {
  let agency: WarningAgency = "IMD";
  let agencyFullName = "India Meteorological Department";
  if (warn.authority === "CWC") {
    agency = "CWC";
    agencyFullName = "Central Water Commission";
  } else if (warn.authority === "DGRE") {
    agency = "DGRE";
    agencyFullName = "Defence Geoinformatics Research Establishment";
  } else if (warn.authority === "SDMA") {
    agency = "IMD";
    agencyFullName = "State Disaster Management Authority (SDMA)";
  }

  let severity: WarningSeverity = "Yellow";
  const sevLower = warn.severity_label.toLowerCase();
  if (sevLower.includes("red") || sevLower.includes("severe") || sevLower.includes("alert")) {
    severity = "Red";
  } else if (sevLower.includes("orange") || sevLower.includes("watch")) {
    severity = "Orange";
  }

  const hazard: WarningHazard = warn.hazard_type === "avalanche" ? "avalanche" : "flood";

  return {
    id: warn.warning_id,
    bulletinCode: warn.warning_id,
    agency,
    agencyFullName,
    title: warn.headline,
    hazard,
    severity,
    affectedSectors: warn.geographic_scope ? [warn.location_id, warn.geographic_scope] : [warn.location_id],
    district: warn.geographic_scope || warn.location_id,
    issuedAt: warn.issued_at,
    validUntil: warn.valid_until,
    summary: warn.summary || warn.headline,
    advisoryNotes: warn.advisory_notes || "Authoritative official advisory issued by authority.",
    sourceReference: warn.source_reference || warn.provenance,
    isReadOnly: true,
  };
}
