export type ReplayViewMode = "replay" | "loading" | "empty";
export type PlaybackSpeed = 1 | 2 | 4;

export interface ReplayFrame {
  id: string;
  timestamp: string;
  phaseLabel: string;
  primaryMetricLabel: string;
  primaryMetricValue: string;
  secondaryMetricLabel: string;
  secondaryMetricValue: string;
  alertTier: string;
  summary: string;
}

export interface HistoricalEvent {
  id: string;
  locationId?: string;
  title: string;
  sector: string;
  hazard: "flood" | "avalanche";
  dateRange: string;
  provenance: string;
  isPersisted?: boolean;
  isDemoFixture?: boolean;
  frames: ReplayFrame[];
}
