export type UnitSystem = "metric" | "imperial";
export type DefaultMapLayer = "standard" | "terrain";
export type RefreshIntervalMin = 5 | 15 | 30;

export interface OperatorPreferences {
  unitSystem: UnitSystem;
  defaultMapLayer: DefaultMapLayer;
  autoRefreshIntervalMin: RefreshIntervalMin;
  staleDataAlerts: boolean;
  highRiskPushAlerts: boolean;
}

export const DEFAULT_PREFERENCES: OperatorPreferences = {
  unitSystem: "metric",
  defaultMapLayer: "standard",
  autoRefreshIntervalMin: 5,
  staleDataAlerts: true,
  highRiskPushAlerts: true,
};
