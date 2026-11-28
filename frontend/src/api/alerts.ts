import { apiClient } from "./client";

export type AlertStatus = "active" | "acknowledged" | "in_progress" | "resolved";
export type AlertHazardType = "flood" | "avalanche";

/**
 * Persisted system-generated operational alert.
 *
 * These are distinct from authoritative IMD/CWC/DGRE bulletins served by
 * `/warnings`: `is_official_warning` is always false for records on `/alerts`.
 */
export interface AlertRecord {
  alert_id: string;
  location_id: string;
  hazard_type: AlertHazardType;
  risk_id: string | null;
  priority_level: string;
  priority_score: number;
  title: string;
  recommendation: string;
  explanation: string[];
  status: AlertStatus;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  action_note: string | null;
  action_updated_at: string | null;
  is_official_warning: boolean;
  created_at: string;
}

export interface AlertListResponse {
  total: number;
  items: AlertRecord[];
}

export interface ListAlertsParams {
  location_id?: string;
  status?: AlertStatus;
  hazard_type?: AlertHazardType;
}

/**
 * List system-generated operational alerts (GET /alerts).
 * Available to every authenticated role.
 */
export async function fetchAlerts(params: ListAlertsParams = {}): Promise<AlertListResponse> {
  const query = new URLSearchParams();
  if (params.location_id) query.set("location_id", params.location_id);
  if (params.status) query.set("status", params.status);
  if (params.hazard_type) query.set("hazard_type", params.hazard_type);

  const qs = query.toString();
  return apiClient<AlertListResponse>(`/alerts${qs ? `?${qs}` : ""}`);
}

/**
 * Acknowledge an operational alert and record the operator identity
 * (POST /alerts/{alert_id}/acknowledge). Requires operator/admin role.
 */
export async function acknowledgeAlert(
  alertId: string,
  note?: string
): Promise<AlertRecord> {
  return apiClient<AlertRecord>(
    `/alerts/${encodeURIComponent(alertId)}/acknowledge`,
    {
      method: "POST",
      body: JSON.stringify(note ? { note } : {}),
    }
  );
}

/**
 * Update the action status and operator note on an alert
 * (PATCH /alerts/{alert_id}/action). Requires operator/admin role.
 */
export async function updateAlertAction(
  alertId: string,
  status: AlertStatus,
  actionNote?: string
): Promise<AlertRecord> {
  return apiClient<AlertRecord>(
    `/alerts/${encodeURIComponent(alertId)}/action`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status,
        ...(actionNote !== undefined ? { action_note: actionNote } : {}),
      }),
    }
  );
}
