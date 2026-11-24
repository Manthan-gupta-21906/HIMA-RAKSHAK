export type ConfidenceLevel = "High" | "Moderate" | "Low";

export type EngineStatus = "warning" | "watch" | "normal" | "insufficient" | "offline";

export type EngineTone = "critical" | "emergency" | "warning" | "clear" | "info" | "neutral";

export type EngineReadiness = "operational" | "limited" | "insufficient";

export type KpiBadgeTone =
  | "imd"
  | "cwc"
  | "dgre"
  | "warning"
  | "emergency"
  | "clear"
  | "neutral";

export type ProgressTone = "emergency" | "warning" | "clear" | "cwc";

export interface EngineMetric {
  label: string;
  value: string;
  hint?: string;
}

export interface EngineProgress {
  label: string;
  valueText: string;
  percent: number;
  tone: ProgressTone;
}

export interface HazardEngine {
  id: "flood" | "avalanche";
  title: string;
  agency: "IMD" | "CWC" | "DGRE";
  status: EngineStatus;
  statusLabel: string;
  confidence: ConfidenceLevel;
  freshness: string;
  provenance: string;
  summary: string;
  metrics: EngineMetric[];
  progress?: EngineProgress;
  note: string;
  noteTone: EngineTone;
  readiness: EngineReadiness;
  readinessLabel: string;
  readinessNote?: string;
  available: boolean;
  actionLabel: string;
}

export interface LocationKpi {
  label: string;
  value: string;
  subtitle: string;
  badge?: string;
  badgeTone?: KpiBadgeTone;
  progressPercent?: number;
  progressTone?: ProgressTone;
}

export interface ExposureProfile {
  population: string;
  elevation: string;
  road: string;
  accessStatus: string;
  accessNote: string;
  facilities: { label: string; value: string }[];
  criticalAssets: string[];
}

export interface FieldDirective {
  status: "done" | "pending" | "warning";
  title: string;
  detail: string;
}

export interface SensorStatus {
  name: string;
  agency: "IMD" | "CWC" | "DGRE";
  status: "online" | "delayed" | "offline";
  detail: string;
}

export interface LocationBulletin {
  agency: "IMD" | "CWC" | "DGRE";
  title: string;
  detail: string;
}

export interface LocationDetail {
  sectorId: string;
  title: string;
  subtitle: string;
  updatedAgo: string;
  consensusPercent: number;
  kpis: LocationKpi[];
  avalanche: HazardEngine;
  flood: HazardEngine;
  exposure: ExposureProfile;
  directives: FieldDirective[];
  sensors: SensorStatus[];
  bulletin: LocationBulletin;
}
