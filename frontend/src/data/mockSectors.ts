export type HazardPathway = "flood" | "avalanche";
export type RiskTier = "High Risk" | "Stage 3" | "Moderate" | "Low";

export interface MonitoringSector {
  id: string;
  name: string;
  district: string;
  elevationM: number;
  lat: number;
  lng: number;
  hazard: HazardPathway;
  threatLabel: string;
  riskTier: RiskTier;
  summaryMetric: string;
  exposureSummary: string;
  confidence: "High" | "Moderate" | "Low";
  updatedAgo: string;
  isStale: boolean;
  isPriority?: boolean;
}

export interface RegionalKpi {
  label: string;
  value: string;
  subtitle: string;
  progressPercent?: number;
}

export const REGIONAL_KPIS: RegionalKpi[] = [
  { label: "Active Alerts", value: "3 Sectors", subtitle: "High observation" },
  { label: "River Jhelum", value: "17.80 ft", subtitle: "Alert mark: 18.0 ft", progressPercent: 98.8 },
  { label: "NH-44 Highway", value: "Restricted", subtitle: "Single lane at Ramban" },
  { label: "Mughal Road", value: "Pass Closed", subtitle: "Pir Ki Gali snow clearance" },
];

export const MOCK_SECTORS: MonitoringSector[] = [
  {
    id: "JK-PN-04",
    name: "Poonch - Surankote",
    district: "Poonch",
    elevationM: 2150,
    lat: 33.643,
    lng: 74.262,
    hazard: "flood",
    threatLabel: "Flash Flood Threat",
    riskTier: "High Risk",
    summaryMetric: "6h Rain: 68 mm | River Level: 17.8 ft (Rising)",
    exposureSummary: "Pop. ~14,200 • Surankote Rd • 2 Clinics",
    confidence: "High",
    updatedAgo: "8m ago",
    isStale: false,
    isPriority: true,
  },
  {
    id: "JK-BM-12",
    name: "Gulmarg - Affarwat",
    district: "Baramulla",
    elevationM: 3980,
    lat: 34.048,
    lng: 74.38,
    hazard: "avalanche",
    threatLabel: "Avalanche Warning",
    riskTier: "Stage 3",
    summaryMetric: "24h Snow: 45 cm | Slope / Wind: 38° • 60 km/h",
    exposureSummary: "Pop. ~3,800 • Tangmarg Ghat Rd • 1 Clinic",
    confidence: "High",
    updatedAgo: "14m ago",
    isStale: false,
    isPriority: true,
  },
  {
    id: "JK-KP-08",
    name: "Kupwara - Machil",
    district: "Kupwara",
    elevationM: 2670,
    lat: 34.651,
    lng: 74.478,
    hazard: "avalanche",
    threatLabel: "Avalanche / Snowpack Watch",
    riskTier: "Moderate",
    summaryMetric: "Last Snow: 28 cm | Telemetry: Offline since 11:00 IST",
    exposureSummary: "Pop. ~6,500 • Machil Pass Rd • 1 PHC",
    confidence: "Low",
    updatedAgo: "3h ago • Stale",
    isStale: true,
    isPriority: true,
  },
  {
    id: "JK-AN-02",
    name: "Anantnag - Sangam Gauge",
    district: "Anantnag",
    elevationM: 1590,
    lat: 33.835,
    lng: 75.072,
    hazard: "flood",
    threatLabel: "Riverine Flood Watch",
    riskTier: "Moderate",
    summaryMetric: "6h Rain: 32 mm | Jhelum Gauge: 16.4 ft (Steady)",
    exposureSummary: "Pop. ~22,000 • NH-44 Corridor • 3 Clinics",
    confidence: "High",
    updatedAgo: "5m ago",
    isStale: false,
  },
  {
    id: "JK-BD-09",
    name: "Bandipora - Gurez Valley",
    district: "Bandipora",
    elevationM: 2420,
    lat: 34.634,
    lng: 74.832,
    hazard: "avalanche",
    threatLabel: "Snowpack Stability Advisory",
    riskTier: "Low",
    summaryMetric: "24h Snow: 14 cm | Razdan Pass: Restricted",
    exposureSummary: "Pop. ~4,100 • Razdan Pass Rd • 1 CHC",
    confidence: "Moderate",
    updatedAgo: "22m ago",
    isStale: false,
  },
];
