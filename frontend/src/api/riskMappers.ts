import type {
  ConfidenceLevel,
  EngineReadiness,
  EngineStatus,
  EngineTone,
  HazardEngine,
  ProgressTone,
} from "../types/location";
import type { LocationRiskState, RiskAssessmentContract } from "./risk";

type Hazard = "flood" | "avalanche";

const HAZARD_META: Record<
  Hazard,
  { title: string; agency: "CWC" | "DGRE"; actionLabel: string }
> = {
  flood: {
    title: "Hydrology & Runoff Engine",
    agency: "CWC",
    actionLabel: "Log Gauge Data",
  },
  avalanche: {
    title: "DGRE Avalanche Model",
    agency: "DGRE",
    actionLabel: "Log Observation",
  },
};

function confidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.75) return "High";
  if (confidence <= 0.4) return "Low";
  return "Moderate";
}

function statusFromRiskClass(
  riskClass: RiskAssessmentContract["risk_class"]
): EngineStatus {
  if (riskClass === "severe" || riskClass === "high") return "warning";
  if (riskClass === "moderate") return "watch";
  if (riskClass === "low") return "normal";
  return "insufficient";
}

function toneFromStatus(status: EngineStatus): EngineTone {
  if (status === "warning") return "emergency";
  if (status === "watch") return "warning";
  if (status === "normal") return "clear";
  return "neutral";
}

function progressToneFromStatus(status: EngineStatus): ProgressTone {
  if (status === "warning") return "emergency";
  if (status === "watch") return "warning";
  if (status === "normal") return "clear";
  return "cwc";
}

function readinessFromAssessment(
  assessment: RiskAssessmentContract
): { readiness: EngineReadiness; label: string } {
  if (assessment.prediction_status === "ready") {
    return { readiness: "operational", label: "Operational" };
  }
  if (assessment.prediction_status === "indicative") {
    return { readiness: "limited", label: "Indicative — limited readiness" };
  }
  if (assessment.prediction_status === "stale") {
    return { readiness: "insufficient", label: "Stale assessment" };
  }
  return { readiness: "insufficient", label: "Unsupported" };
}

/**
 * Convert a persisted risk assessment into the existing HazardEngine card
 * contract. Flood and avalanche are always mapped independently — the two
 * pathways are never merged or used to fill each other's gaps.
 */
export function mapAssessmentToHazardEngine(
  hazard: Hazard,
  assessment: RiskAssessmentContract | null | undefined
): HazardEngine {
  const meta = HAZARD_META[hazard];

  if (!assessment) {
    return {
      id: hazard,
      title: meta.title,
      agency: meta.agency,
      status: "insufficient",
      statusLabel: "No Assessment",
      confidence: "Low",
      freshness: "Unknown",
      provenance: "No persisted assessment",
      summary: `No persisted ${hazard} assessment has been recorded for this location.`,
      metrics: [],
      note: `Run a controlled ${hazard} assessment once observations are available. This panel is not an official warning.`,
      noteTone: "neutral",
      readiness: "insufficient",
      readinessLabel: "No persisted assessment",
      available: false,
      actionLabel: meta.actionLabel,
    };
  }

  const status = statusFromRiskClass(assessment.risk_class);
  const { readiness, label: readinessLabel } = readinessFromAssessment(assessment);
  const available =
    assessment.risk_class !== "unsupported" &&
    assessment.prediction_status !== "unsupported";

  const scoreText =
    assessment.score !== null ? `${(assessment.score * 100).toFixed(0)}%` : "Not available";

  const metrics = [
    { label: "Risk Class", value: assessment.risk_class },
    { label: "Hazard Score", value: scoreText },
    {
      label: "Confidence",
      value: `${(assessment.confidence * 100).toFixed(0)}%`,
    },
    { label: "Lead Time", value: `${assessment.lead_time_hours}h` },
    {
      label: "Assessed",
      value: new Date(assessment.assessed_at).toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      }),
    },
    { label: "Model", value: assessment.model_version ?? "—" },
  ];

  const note =
    assessment.readiness_reason ??
    (assessment.freshness === "stale"
      ? "This assessment is stale; treat it as indicative until refreshed."
      : assessment.prediction_status === "indicative"
        ? "Model readiness is indicative; corroborate with field observations."
        : "Assessment is current and ready for operational review.");

  return {
    id: hazard,
    title: meta.title,
    agency: meta.agency,
    status,
    statusLabel:
      assessment.risk_class === "unsupported"
        ? "Unsupported"
        : assessment.risk_class.charAt(0).toUpperCase() +
          assessment.risk_class.slice(1),
    confidence: confidenceLevel(assessment.confidence),
    freshness:
      assessment.freshness.charAt(0).toUpperCase() + assessment.freshness.slice(1),
    provenance: `${assessment.provenance.source_name} • ${assessment.provenance.licence}${
      assessment.provenance.is_demo_fixture ? " • Demo Fixture" : ""
    }`,
    summary: `Persisted ${hazard} assessment from the backend risk pathway.`,
    metrics,
    progress:
      assessment.score !== null
        ? {
            label: "Hazard Score",
            valueText: scoreText,
            percent: Math.min(100, Math.max(0, assessment.score * 100)),
            tone: progressToneFromStatus(status),
          }
        : undefined,
    note,
    noteTone: toneFromStatus(status),
    readiness,
    readinessLabel,
    readinessNote: assessment.readiness_reason ?? undefined,
    available,
    actionLabel: meta.actionLabel,
  };
}

/** Map a unified risk state into independent flood and avalanche engine cards. */
export function mapRiskStateToHazardEngines(
  riskState: LocationRiskState | null | undefined
): { flood: HazardEngine; avalanche: HazardEngine } {
  return {
    flood: mapAssessmentToHazardEngine("flood", riskState?.flood),
    avalanche: mapAssessmentToHazardEngine("avalanche", riskState?.avalanche),
  };
}
