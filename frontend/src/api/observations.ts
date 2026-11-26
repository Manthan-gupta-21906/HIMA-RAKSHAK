import { apiClient } from "./client";

export interface ObservationContract {
  observation_id: string;
  location_id: string;
  source_id: string;
  observed_at: string;
  metric: string;
  value: number;
  unit: string;
  is_demo_fixture: boolean;
}

export interface ObservationListResponse {
  total: number;
  items: ObservationContract[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  };
}

export interface ListObservationsParams {
  location_id: string;
  metric?: string;
  since?: string;
  until?: string;
  page?: number;
  page_size?: number;
}

export async function fetchObservations(params: ListObservationsParams): Promise<ObservationListResponse> {
  const query = new URLSearchParams({ location_id: params.location_id });
  if (params.metric) query.set("metric", params.metric);
  if (params.since) query.set("since", params.since);
  if (params.until) query.set("until", params.until);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));

  return apiClient<ObservationListResponse>(`/observations?${query.toString()}`);
}

export interface ObservationSubmissionPayload {
  /** Backend accepts both location_id and sector_id via AliasChoices */
  sector_id: string;
  hazard_type: string;
  metric?: string;
  value: number;
  unit: string;
  notes?: string;
  observed_at?: string;
}

/**
 * Submit a field observation to POST /observations.
 * Requires an operator or admin Bearer token (set by AuthContext).
 * Returns the persisted ObservationContract on success.
 */
export async function submitObservation(
  payload: ObservationSubmissionPayload,
): Promise<ObservationContract> {
  return apiClient<ObservationContract>("/observations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
