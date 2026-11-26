export type HazardPathway = "flood" | "avalanche";
export type RiskTier = "High Risk" | "Stage 3" | "Moderate" | "Low" | "Unsupported";

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
    id: "JK-SGR-01",
    name: "Srinagar — Jhelum Floodplain",
    district: "Srinagar District, J&K",
    elevationM: 1585,
    lat: 34.0837,
    lng: 74.7973,
    hazard: "flood",
    threatLabel: "Riverine Flood Threat",
    riskTier: "High Risk",
    summaryMetric: "6h Rain: 45 mm | River Level: 4.8 m (Rising)",
    exposureSummary: "Pop. ~18,500 • Jhelum Bund Rd • 3 Clinics",
    confidence: "High",
    updatedAgo: "8m ago",
    isStale: false,
    isPriority: true,
  },
  {
    id: "JK-GUL-01",
    name: "Gulmarg — Affarwat Ridge",
    district: "Baramulla District, J&K",
    elevationM: 3980,
    lat: 34.0484,
    lng: 74.3805,
    hazard: "avalanche",
    threatLabel: "Avalanche Warning",
    riskTier: "Stage 3",
    summaryMetric: "Snow Depth: 110 cm | Slope / Wind: 38° • 55 km/h",
    exposureSummary: "Pop. ~3,800 • Tangmarg Ghat Rd • 1 Clinic",
    confidence: "High",
    updatedAgo: "14m ago",
    isStale: false,
    isPriority: true,
  },
  {
    id: "JK-BAN-01",
    name: "Banihal — NH-44 Corridor",
    district: "Ramban District, J&K",
    elevationM: 1666,
    lat: 33.4375,
    lng: 75.1947,
    hazard: "flood",
    threatLabel: "Dual-Hazard Corridor Watch",
    riskTier: "Moderate",
    summaryMetric: "Rain: 32 mm | Snow: 35 cm • Cached Telemetry",
    exposureSummary: "Pop. ~9,400 • NH-44 Corridor • 2 Clinics",
    confidence: "Moderate",
    updatedAgo: "2h ago • Stale",
    isStale: true,
    isPriority: true,
  },
  {
    id: "JK-DRS-01",
    name: "Drass — Zojila High Pass",
    district: "Kargil / Ganderbal Border Sector",
    elevationM: 3528,
    lat: 34.4275,
    lng: 75.7525,
    hazard: "avalanche",
    threatLabel: "Unsupported Coverage",
    riskTier: "Low",
    summaryMetric: "Insufficient local sensor and snowpack coverage",
    exposureSummary: "Pop. ~2,100 • Zojila Pass Rd • 1 PHC",
    confidence: "Low",
    updatedAgo: "Offline",
    isStale: true,
  },
];
