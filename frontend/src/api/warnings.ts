import { apiClient } from "./client";

export interface OfficialWarningContract {
  warning_id: string;
  authority: "CWC" | "IMD" | "DGRE" | "SDMA";
  hazard_type: "flood" | "avalanche";
  location_id: string;
  severity_label: string;
  headline: string;
  issued_at: string;
  valid_until: string;
  is_read_only: boolean;
  provenance: string;
  geographic_scope?: string | null;
  summary?: string | null;
  advisory_notes?: string | null;
  source_url?: string | null;
  source_reference?: string | null;
  is_demo_fixture: boolean;
  is_expired: boolean;
}

export interface WarningListResponse {
  total: number;
  items: OfficialWarningContract[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  };
}

export interface ListWarningsParams {
  location_id?: string;
  hazard_type?: string;
  authority?: string;
  is_expired?: boolean;
  page?: number;
  page_size?: number;
}

export async function fetchWarnings(params: ListWarningsParams = {}): Promise<WarningListResponse> {
  const query = new URLSearchParams();
  if (params.location_id) query.set("location_id", params.location_id);
  if (params.hazard_type) query.set("hazard_type", params.hazard_type);
  if (params.authority) query.set("authority", params.authority);
  if (params.is_expired !== undefined) query.set("is_expired", String(params.is_expired));
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));

  const qs = query.toString();
  return apiClient<WarningListResponse>(`/warnings${qs ? `?${qs}` : ""}`);
}

export async function fetchWarningDetail(warningId: string): Promise<OfficialWarningContract> {
  return apiClient<OfficialWarningContract>(`/warnings/${encodeURIComponent(warningId)}`);
}
