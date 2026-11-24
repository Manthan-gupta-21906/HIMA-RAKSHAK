import { MOCK_SECTORS, type MonitoringSector } from "../data/mockSectors";
import type { HazardKind } from "../types/observation";

export interface SectorOption {
  value: string;
  label: string;
  elevation: string;
}

export interface ThreatAdvisory {
  kind: HazardKind;
  label: string;
  tier: string;
}

export interface ObserverIdentity {
  id: string;
  name: string;
  role: string;
  station: string;
  district: string;
  device: string;
}

export interface ObservationFormDefaults {
  sectors: SectorOption[];
  observer: ObserverIdentity;
  threatAdvisory: Record<string, ThreatAdvisory>;
}

export const SECTOR_OPTIONS: SectorOption[] = MOCK_SECTORS.map((sector) => ({
  value: sector.id,
  label: `${sector.name} (${sector.id}) • Elev. ${sector.elevationM}m`,
  elevation: String(sector.elevationM),
}));

export const DEFAULT_OBSERVER: ObserverIdentity = {
  id: "usr-sdrf-04",
  name: "Sub-Inspector R. Ahmed",
  role: "field_officer",
  station: "SDRF Ground Unit 04",
  district: "Poonch - Surankote",
  device: "Ruggedized Field Terminal #JKS-094",
};

export const THREAT_ADVISORY: Record<string, ThreatAdvisory> = {
  "JK-PN-04": { kind: "avalanche", label: "Avalanche Stage-2 (Orange Alert)", tier: "Stage 2" },
  "JK-BM-12": { kind: "avalanche", label: "Avalanche Stage-3 (Red Alert)", tier: "Stage 3" },
  "JK-KP-08": { kind: "avalanche", label: "Avalanche Watch (Moderate)", tier: "Watch" },
  "JK-AN-02": { kind: "flood", label: "Riverine Flood Watch", tier: "Watch" },
  "JK-BD-09": { kind: "avalanche", label: "Snowpack Stability Advisory", tier: "Low" },
};

export function getSectorById(sectorId: string): MonitoringSector | undefined {
  return MOCK_SECTORS.find((sector) => sector.id === sectorId);
}

export function getThreatAdvisory(sectorId: string): ThreatAdvisory {
  return (
    THREAT_ADVISORY[sectorId] ?? {
      kind: "avalanche",
      label: "No active advisory",
      tier: "None",
    }
  );
}
