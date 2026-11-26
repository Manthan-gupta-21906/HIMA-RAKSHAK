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
