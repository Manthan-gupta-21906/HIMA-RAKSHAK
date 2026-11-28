import { apiClient } from "./client";

export interface SourceOut {
  source_id: string;
  source_name: string;
  provider: string;
  dataset: string;
  source_type: "weather" | "hydrology" | "snow" | "terrain" | "official_warning" | "field_observation" | string;
  access_mode: "live" | "cached" | "sample" | string;
  licence: string;
  reference_url?: string;
  update_frequency_minutes: number;
  trust_classification: "authoritative" | "institutional" | "community" | "demo" | string;
  is_authoritative: boolean;
  is_demo_fixture: boolean;
  freshness: "fresh" | "stale" | "unknown";
  last_fetched_at?: string | null;
  created_at: string;
}

export interface SourceListResponse {
  total: number;
  items: SourceOut[];
}

export interface ListSourcesParams {
  source_type?: string;
  access_mode?: string;
}

export interface SourceCreatePayload {
  source_id: string;
  source_name?: string;
  provider?: string;
  dataset?: string;
  source_type: string;
  access_mode?: string;
  licence: string;
  reference_url?: string;
  update_frequency_minutes: number;
  trust_classification?: string;
  is_authoritative?: boolean;
  is_demo_fixture?: boolean;
}

/**
 * Fetch registered data sources from the backend registry (GET /sources).
 */
export async function fetchSources(params: ListSourcesParams = {}): Promise<SourceListResponse> {
  const query = new URLSearchParams();
  if (params.source_type) query.set("source_type", params.source_type);
  if (params.access_mode) query.set("access_mode", params.access_mode);

  const qs = query.toString();
  return apiClient<SourceListResponse>(`/sources${qs ? `?${qs}` : ""}`);
}

/**
 * Fetch a single source's detail from backend (GET /sources/{source_id}).
 */
export async function fetchSourceDetail(sourceId: string): Promise<SourceOut> {
  return apiClient<SourceOut>(`/sources/${encodeURIComponent(sourceId)}`);
}

/**
 * Record a fetch for a source (POST /sources/{source_id}/fetch). Requires admin role.
 */
export async function refreshSource(sourceId: string): Promise<SourceOut> {
  return apiClient<SourceOut>(
    `/sources/${encodeURIComponent(sourceId)}/fetch`,
    { method: "POST" }
  );
}

/**
 * Register a new data source (POST /sources). Requires admin role.
 */
export async function registerSource(payload: SourceCreatePayload): Promise<SourceOut> {
  return apiClient<SourceOut>("/sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
