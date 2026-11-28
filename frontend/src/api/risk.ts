import { apiClient } from "./client";

export interface ProvenanceMeta {
  source_id: string;
  source_name: string;
  licence: string;
  is_demo_fixture: boolean;
  ingested_at: string;
}

export interface RiskAssessmentContract {
  risk_id: string;
  location_id: string;
  hazard_type: "flood" | "avalanche";
  risk_class: "low" | "moderate" | "high" | "severe" | "unsupported";
  score: number | null;
  confidence: number;
  lead_time_hours: number;
  freshness: "fresh" | "stale" | "unknown";
  prediction_status: "ready" | "indicative" | "stale" | "unsupported";
  readiness_reason?: string | null;
  assessed_at: string;
  model_version?: string | null;
  provenance: ProvenanceMeta;
}

export interface LocationRiskState {
  location_id: string;
  updated_at: string;
  flood?: RiskAssessmentContract | null;
  avalanche?: RiskAssessmentContract | null;
  primary_hazard?: "flood" | "avalanche" | null;
  highest_risk_class: "low" | "moderate" | "high" | "severe" | "unsupported";
}

export interface RiskHistoryResponse {
  total: number;
  items: RiskAssessmentContract[];
  pagination?: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  } | null;
}

export type ExposureCoverageStatus = "complete" | "partial" | "unknown";

export interface ExposureAsset {
  asset_id: string;
  asset_type: string;
  name: string;
  count: number;
  count_type: "verified" | "estimated";
  population_affected: number;
  is_critical: boolean;
  metadata: Record<string, string | number | boolean>;
}

/** Spatial exposure profile returned by GET /risk/exposure/{location_id}. */
export interface LocationExposureProfile {
  location_id: string;
  evaluated_at: string;
  coverage_status: ExposureCoverageStatus;
  population_exposed: number;
  settlements_count: number;
  homes_exposed: number;
  roads_exposed_km: number;
  critical_facilities_count: number;
  assets: ExposureAsset[];
  missing_layers: string[];
}

/** Explainable priority assessment returned by GET /risk/priority/{location_id}. */
export interface PriorityAssessment {
  location_id: string;
  evaluated_at: string;
  hazard_score: number | null;
  hazard_risk_class: "low" | "moderate" | "high" | "severe" | "unsupported";
  exposure_score: number;
  impact_score: number;
  priority_score: number;
  coverage_status: ExposureCoverageStatus;
  priority_level: string;
  confidence: number;
  freshness: "fresh" | "stale" | "unknown";
  prediction_status: "ready" | "indicative" | "stale" | "unsupported";
  weights_used: Record<string, number>;
  breakdown: Record<string, number>;
  explanation: string[];
}

/**
 * Fetch unified multi-hazard risk state for a location (GET /risk/state/{location_id})
 */
export async function fetchLocationRiskState(locationId: string): Promise<LocationRiskState> {
  return apiClient<LocationRiskState>(`/risk/state/${encodeURIComponent(locationId)}`);
}

/**
 * Fetch latest assessment per hazard type for a location (GET /risk/current/{location_id})
 */
export async function fetchCurrentRisk(
  locationId: string
): Promise<Record<string, RiskAssessmentContract | null>> {
  return apiClient<Record<string, RiskAssessmentContract | null>>(
    `/risk/current/${encodeURIComponent(locationId)}`
  );
}

/**
 * Fetch paginated risk assessment history for a location (GET /risk/history/{location_id})
 */
export async function fetchRiskHistory(
  locationId: string,
  params: {
    hazard_type?: "flood" | "avalanche";
    since?: string;
    page?: number;
    page_size?: number;
  } = {}
): Promise<RiskHistoryResponse> {
  const query = new URLSearchParams();
  if (params.hazard_type) query.set("hazard_type", params.hazard_type);
  if (params.since) query.set("since", params.since);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));

  const qs = query.toString();
  return apiClient<RiskHistoryResponse>(
    `/risk/history/${encodeURIComponent(locationId)}${qs ? `?${qs}` : ""}`
  );
}

/**
 * Fetch spatial exposure for a location (GET /risk/exposure/{location_id}).
 */
export async function fetchLocationExposure(
  locationId: string
): Promise<LocationExposureProfile> {
  return apiClient<LocationExposureProfile>(
    `/risk/exposure/${encodeURIComponent(locationId)}`
  );
}

/**
 * Fetch the explainable priority assessment for a location
 * (GET /risk/priority/{location_id}).
 */
export async function fetchLocationPriority(
  locationId: string
): Promise<PriorityAssessment> {
  return apiClient<PriorityAssessment>(
    `/risk/priority/${encodeURIComponent(locationId)}`
  );
}

export interface ReplayFrameContract {
  id: string;
  timestamp: string;
  phase_label: string;
  primary_metric_label: string;
  primary_metric_value: string;
  secondary_metric_label: string;
  secondary_metric_value: string;
  alert_tier: string;
  risk_class: string;
  score: number | null;
  confidence: number;
  summary: string;
}

export interface ReplayEventContract {
  id: string;
  location_id: string;
  title: string;
  sector: string;
  hazard: "flood" | "avalanche";
  date_range: string;
  provenance: string;
  is_demo_fixture: boolean;
  frames: ReplayFrameContract[];
}

export interface ReplayEventsResponse {
  total: number;
  items: ReplayEventContract[];
}

/**
 * Fetch chronological historical replay sequences reconstructed from persisted
 * risk assessment history (GET /risk/replay).
 */
export async function fetchReplayEvents(
  params: {
    location_id?: string;
    hazard_type?: "flood" | "avalanche";
    since?: string;
    limit?: number;
  } = {}
): Promise<ReplayEventsResponse> {
  const query = new URLSearchParams();
  if (params.location_id) query.set("location_id", params.location_id);
  if (params.hazard_type) query.set("hazard_type", params.hazard_type);
  if (params.since) query.set("since", params.since);
  if (params.limit) query.set("limit", String(params.limit));

  const qs = query.toString();
  return apiClient<ReplayEventsResponse>(
    `/risk/replay${qs ? `?${qs}` : ""}`
  );
}

export interface RiskEvaluationResponse {
  location_id: string;
  risk_state: LocationRiskState;
  exposure: {
    location_id: string;
    population_exposed: number;
    roads_exposed_km: number;
    critical_facilities_count: number;
    coverage_status: string;
  };
  priority: {
    location_id: string;
    priority_level: string;
    priority_score: number;
    hazard_risk_class: string;
    prediction_status: string;
    explanation: string[];
  };
  alert?: {
    alert_id: string;
    priority_level: string;
    title: string;
  } | null;
}

/**
 * Trigger controlled observation -> risk -> exposure -> priority -> alert evaluation
 * (POST /risk/evaluate/{location_id}).
 */
export async function evaluateLocationRisk(
  locationId: string,
  triggerAlert = true
): Promise<RiskEvaluationResponse> {
  return apiClient<RiskEvaluationResponse>(
    `/risk/evaluate/${encodeURIComponent(locationId)}?trigger_alert=${triggerAlert}`,
    {
      method: "POST",
    }
  );
}
