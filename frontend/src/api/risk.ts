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

export interface ReplayFrameContract {
  id: string;
  timestamp: string;
  phase_label: string;
  primary_metric_label: string;
  primary_metric_value: string;
  secondary_metric_label: string;
  secondary_metric_value: string;
  alert_tier: string;
  risk_class: "low" | "moderate" | "high" | "severe" | "unsupported";
  score: number | null;
  confidence: number;
  summary: string;
}

export interface BackendHistoricalReplayEvent {
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
  items: BackendHistoricalReplayEvent[];
}

/**
 * Fetch chronological historical replay sequences reconstructed from persisted history (GET /risk/replay).
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
  return apiClient<ReplayEventsResponse>(`/risk/replay${qs ? `?${qs}` : ""}`);
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
