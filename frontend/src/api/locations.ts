import { apiClient } from "./client";

export interface LocationOut {
  location_id: string;
  name: string;
  admin_unit: string;
  latitude: number;
  longitude: number;
  geometry_geojson?: Record<string, unknown> | null;
  geom?: { type: string; coordinates: [number, number] } | null;
  supported_hazards: string[];
  coverage_status: "supported" | "partial" | "unsupported";
  coverage_note?: string | null;
  is_demo_fixture: boolean;
  provenance: string;
}

export interface LocationListResponse {
  total: number;
  items: LocationOut[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  };
}

export interface ListLocationsParams {
  q?: string;
  hazard_type?: string;
  coverage_status?: string;
  page?: number;
  page_size?: number;
}

export interface LocationCreatePayload {
  location_id: string;
  name: string;
  admin_unit: string;
  latitude: number;
  longitude: number;
  supported_hazards: string[];
  coverage_status: "supported" | "partial" | "unsupported";
  coverage_note: string;
}

export interface LocationCoverageUpdatePayload {
  coverage_status: "supported" | "partial" | "unsupported";
  coverage_note: string;
}

export async function fetchLocations(params: ListLocationsParams = {}): Promise<LocationListResponse> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.hazard_type) query.set("hazard_type", params.hazard_type);
  if (params.coverage_status) query.set("coverage_status", params.coverage_status);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));

  const qs = query.toString();
  return apiClient<LocationListResponse>(`/locations${qs ? `?${qs}` : ""}`);
}

export async function fetchLocationDetail(locationId: string): Promise<LocationOut> {
  return apiClient<LocationOut>(`/locations/${encodeURIComponent(locationId)}`);
}

/**
 * Register a pilot location (POST /locations). Requires admin role.
 */
export async function createLocation(payload: LocationCreatePayload): Promise<LocationOut> {
  return apiClient<LocationOut>("/locations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Update coverage status and note for a location
 * (PATCH /locations/{location_id}/coverage). Requires admin role.
 */
export async function updateLocationCoverage(
  locationId: string,
  payload: LocationCoverageUpdatePayload
): Promise<LocationOut> {
  return apiClient<LocationOut>(
    `/locations/${encodeURIComponent(locationId)}/coverage`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}
