export type HazardKind = "avalanche" | "flood";

export interface HazardMetricConfig {
  label: string;
  unit: string;
  min: number;
  max: number;
  placeholder: string;
}

export interface ObservationValidationError {
  code: string;
  message: string;
  detail?: string;
}

export interface ObservationState {
  sectorId: string;
  hazardKind: HazardKind;
  observationValue: string;
  notes: string;
  submitted: boolean;
  submitting: boolean;
  error: ObservationValidationError | null;
}

export interface ObservationResult {
  sectorId: string;
  sectorName: string;
  hazardKind: HazardKind;
  value: number;
  unit: string;
  notes: string;
  observedAt: string;
  observerId: string;
  observerName: string;
}

export const HAZARD_CONFIG: Record<HazardKind, HazardMetricConfig> = {
  avalanche: {
    label: "Fresh Snow Accumulation (Past 6 hrs)",
    unit: "cm snow",
    min: 0,
    max: 350,
    placeholder: "e.g. 48.0",
  },
  flood: {
    label: "River Gauge Depth (Past 6 hrs)",
    unit: "ft water",
    min: 0,
    max: 50,
    placeholder: "e.g. 12.5",
  },
};

export const VALIDATION_ERROR_CODES = {
  REQUIRED: "E-400",
  OUT_OF_RANGE: "E-401",
  NON_NUMERIC: "E-402",
} as const;
